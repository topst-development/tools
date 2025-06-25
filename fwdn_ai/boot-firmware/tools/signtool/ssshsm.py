##
# SSS HSM
#
import struct
import binascii
from argparse import ArgumentParser
from hashlib import sha256
from ecdsa import SigningKey, VerifyingKey, NIST256p
from Crypto.Cipher import AES
from Crypto.Hash import CMAC
from tcckeys import tcckeys, KEY_BASE, HKEY_NAME

SSSHSM_HEADER_FORMAT = "<LLLL"
SSSHSM_HEADER_LENGTH = struct.calcsize(SSSHSM_HEADER_FORMAT)

SSSHSM_FOOTER_FORMAT = "<L64s64s12s"
SSSHSM_FOOTER_LENGTH = struct.calcsize(SSSHSM_FOOTER_FORMAT)
SSSHSM_FOOTER_SIGNATURE_OFFSET = 68

SSSHSM_CMAC_LENGTH = 16
MF_PASSWORD_OFFSET = 28
MF_PASSWORD_LENGTH = 16

SSSHSM_ALGO_INFO = 0x2313

HSMIV = b"\x30\x31\x30\x0D\x06\x09\x60\x86\x48\x01\x65\x03\x04\x02\x01\x05"

def impl_sign(imgbuf, keybuf):
    return SigningKey.from_string(
                keybuf, curve = NIST256p, hashfunc = sha256).sign(imgbuf)

def impl_verify(imgbuf, keybuf, signature):
    return VerifyingKey.from_string(
                keybuf, curve = NIST256p, hashfunc = sha256).verify(signature, imgbuf)

def impl_cmac(imgbuf, keybuf):
    cmac = CMAC.new(keybuf, ciphermod=AES)
    cmac.update(imgbuf)
    return cmac.digest()

def impl_encrypt(imgbuf, keybuf):
    return AES.new(keybuf, AES.MODE_CBC, HSMIV).encrypt(imgbuf)

def impl_decrypt(imgbuf, keybuf):
    return AES.new(keybuf, AES.MODE_CBC, HSMIV).decrypt(imgbuf)

def tcc_sign(keybuf, imgbuf):
    return impl_sign(imgbuf, keybuf)

def tcc_verify(keybuf, imgbuf, signature):
    return impl_verify(imgbuf, keybuf, signature)

def tcc_cmac(keybuf, imgbuf):
    return impl_cmac(imgbuf, keybuf)

def tcc_encrypt(keybuf, imgbuf):
    return impl_encrypt(imgbuf, keybuf)

def tcc_decrypt(keybuf, imgbuf):
    return impl_decrypt(imgbuf, keybuf)

## signer class
#
class signer:
    def __init__(self, src, rbid, fac, pw, keybase=KEY_BASE):
        self.fac = fac
        self.pw = pw
        self.rbid = rbid
        self.hkey = tcckeys(HKEY_NAME, keybase)
        with open(src, "rb") as f:
            self.header = list(struct.unpack(SSSHSM_HEADER_FORMAT, f.read(SSSHSM_HEADER_LENGTH)))
            length = self.header[3] - SSSHSM_HEADER_LENGTH
            self.img_buf = tcc_decrypt(bytearray(32), f.read(length))[:-SSSHSM_FOOTER_LENGTH]
            f.read(SSSHSM_CMAC_LENGTH)
            self.append = f.read()

    def proc_ssshsm(self, out):
        self.header[1] = self.rbid
        if self.fac == True:
            buf = struct.pack(SSSHSM_HEADER_FORMAT, *self.header) + self.img_buf[:MF_PASSWORD_OFFSET]
            buf += bytes(self.pw, 'utf-8')
            pad_size = MF_PASSWORD_LENGTH - (len(self.pw) % MF_PASSWORD_LENGTH)
            buf += bytearray(pad_size)
            buf += self.img_buf[MF_PASSWORD_OFFSET + MF_PASSWORD_LENGTH:]
        else:
            buf = struct.pack(SSSHSM_HEADER_FORMAT, *self.header) + self.img_buf
        buf += struct.pack("<L64s", SSSHSM_ALGO_INFO, self.hkey.getverifykey())
        buf += tcc_sign(self.hkey.getsignkey(), buf) + bytearray(12)
        enckey = self.hkey.getenc256key() if self.fac == False else bytearray(32)
        buf = buf[:SSSHSM_HEADER_LENGTH] + tcc_encrypt(enckey, buf[SSSHSM_HEADER_LENGTH:])
        cmac = tcc_cmac(enckey, buf)
        out.write(buf)
        out.write(cmac + self.append)

    def process(self, name):
        with open(name, "wb") as out:
            self.proc_ssshsm(out)

## verifier class
#
class verifier:
    def __init__(self, keybase=KEY_BASE):
        self.hkey = tcckeys(HKEY_NAME, keybase)

    def proc_ssshsm(self, f):
        buf = f.read(SSSHSM_HEADER_LENGTH)
        self.header = list(struct.unpack(SSSHSM_HEADER_FORMAT, buf))
        length = self.header[3] - SSSHSM_HEADER_LENGTH
        img_buf = f.read(length)
        cmac = f.read(SSSHSM_CMAC_LENGTH)
        self.append = f.read()
        cmacres = False
        if cmac == tcc_cmac(bytearray(32), buf + img_buf):
            buf += tcc_decrypt(bytearray(32), img_buf)
            enc = False
            cmacres = True
        elif cmac ==  tcc_cmac(self.hkey.getenc256key(), buf + img_buf):
            buf += tcc_decrypt(self.hkey.getenc256key(), img_buf)
            enc = True
            cmacres = True
        footer = list(struct.unpack(SSSHSM_FOOTER_FORMAT, buf[-SSSHSM_FOOTER_LENGTH:]))

        print("[SSS HSM]")
        print("  - Encrypted   : {}".format(enc))
        print("  - Rollback ID : {}".format(self.header[1]))
        print("  - Blocks      : {}".format(self.header[2]))
        print("  - Size        : {} bytes".format(self.header[3]))
        print("  - Algorithm   : {}".format(hex(footer[0])))
        res = True if footer[1] == self.hkey.getverifykey() else False
        print("  - PubKey      : {} ({})".format(binascii.hexlify(footer[1]), res))
        res = tcc_verify(self.hkey.getverifykey(), buf[:-(SSSHSM_FOOTER_LENGTH-SSSHSM_FOOTER_SIGNATURE_OFFSET)], footer[2])
        print("  - Signature   : {} ({})".format(binascii.hexlify(footer[2]), res))
        print("  - CMAC        : {} ({})".format(binascii.hexlify(cmac), cmacres))

    def process(self, name):
        with open(name, "rb") as f:
            self.proc_ssshsm(f)

## Start Code
#
if (__name__ == "__main__"):
    parser = ArgumentParser(description="SSS-HSM Sign Tool")
    parser.add_argument("-k", "--keybase", type=str, default=KEY_BASE, \
            help="keys directory")
    parser.add_argument("-i", "--input", type=str, \
            help="input file name")
    parser.add_argument("-o", "--output", type=str, \
            help="output file name (Default: [input file name].secure)")
    parser.add_argument("-r", "--rbid", type=int, default=0, \
            help="rollback protection id")
    parser.add_argument("-f", "--factory", action="store_true", default=False, \
            help="encryption")
    parser.add_argument("-p", "--password", type=str, \
            help="input factory mode encryption password.(MAX 16 bytes)")
    parser.add_argument("-v", "--verify", type=str, \
            help="input file name for verification")
    args = parser.parse_args()

    if args.verify is None:
        if args.output is None:
            args.output = args.input + ".factory" if args.factory else args.input + ".secure"
        signer(args.input, args.rbid, args.factory, args.password, args.keybase).process(args.output)
    else:
        verifier(args.keybase).process(args.verify)
