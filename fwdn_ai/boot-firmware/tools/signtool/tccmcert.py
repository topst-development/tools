##
# TCC MCERT
#
import struct
import binascii
import hashlib
from argparse import ArgumentParser
from hashlib import sha256
from ecdsa import SigningKey, VerifyingKey, NIST256p
from Crypto.Cipher import AES
from tcckeys import tcckeys, KEY_BASE, HKEY_NAME, RKEY_NAME, MKEY_NAME, IKEY_NAME
from tccscram import tccscram
from Crypto.Random import get_random_bytes

TCC_MCERT_MARKER = b"MCERT"
TCC_MCERT_FORMAT = "<5s7sL4s12sBBBB16s8sL64s16s48s256s"
TCC_MCERT_LENGTH = struct.calcsize(TCC_MCERT_FORMAT)
TCC_MCERT_IV_OFFSET = 36
TCC_MCERT_ENC_OFFSET = 64
TCC_MCERT_IV_SIZE = 16
TCC_MCERT_SALT_SIZE = 16

TCC_MF_FORMAT = "<16s16s64s32s64s16s16s16s16s"
TCC_MF_LENGTH = struct.calcsize(TCC_MF_FORMAT)

FACTORY_ENCRYPTION = 0x80

MF_PASSWORD_LENGTH = 16

def impl_cbc_encrypt(imgbuf, keybuf, ivbuf):
    return AES.new(keybuf, AES.MODE_CBC, ivbuf).encrypt(imgbuf)

def impl_sign(imgbuf, keybuf):
    return SigningKey.from_string(
                keybuf, curve = NIST256p, hashfunc = sha256).sign(imgbuf)

def impl_verify(imgbuf, keybuf, signature):
    return VerifyingKey.from_string(
                keybuf, curve = NIST256p, hashfunc = sha256).verify(signature, imgbuf)

def impl_encrypt(imgbuf, enckey, iv):
    return AES.new(enckey, AES.MODE_CBC, iv).encrypt(imgbuf)

def impl_decrypt(imgbuf, enckey, iv):
    return AES.new(enckey, AES.MODE_CBC, iv).decrypt(imgbuf)

def reverse(strval):
    revval = type(strval)()
    if type(revval) == str:
        for i in range(len(strval),0,-1):
            revval += strval[i-1]
    else:
        for i in range(len(strval),0,-1):
            revval += bytes([strval[i-1]])
    return revval

def tcc_sign(keybuf, imgbuf):
    return impl_sign(imgbuf, keybuf)

def tcc_verify(keybuf, imgbuf, signature):
    return impl_verify(imgbuf, keybuf, signature)

def tcc_cbc_encrypt(keybuf, ivbuf, imgbuf):
    return impl_cbc_encrypt(imgbuf, keybuf, ivbuf)

def tcc_encrypt(keybuf, imgbuf, iv):
    return impl_encrypt(imgbuf, reverse(keybuf), iv)

def tcc_decrypt(keybuf, imgbuf, iv):
    return impl_decrypt(imgbuf, reverse(keybuf), iv)

## signer class
#
class signer:
    def __init__(self, enc, rbid, fac, pw, keybase=KEY_BASE):
        self.fac = fac
        self.enc = enc
        self.rbid = rbid
        self.pw = pw
        self.hkey = tcckeys(HKEY_NAME, keybase)
        self.rkey = tcckeys(RKEY_NAME, keybase)
        self.mkey = tcckeys(MKEY_NAME, keybase)
        self.mcert = list(struct.unpack(TCC_MCERT_FORMAT, bytearray(TCC_MCERT_LENGTH)))

    def proc_mcert(self, out):
        iv = get_random_bytes(16)
        self.mcert[0] = TCC_MCERT_MARKER
        self.mcert[9] = iv
        self.mcert[11] = self.rbid
        self.mcert[12] = self.mkey.getverifykey()
        self.mcert[13] = self.mkey.getenc128key()
        buf = struct.pack(TCC_MCERT_FORMAT, *self.mcert)
        signature = tcc_sign(self.rkey.getsignkey(), buf)
        if self.fac:
            mf = list(struct.unpack(TCC_MF_FORMAT, bytearray(TCC_MF_LENGTH)))
            mf[2] = self.hkey.getverifykey() # HSM Verification Key
            mf[3] = self.hkey.getenc256key() # HSM Encryption Key
            mf[4] = self.rkey.getverifykey() # MCERT Verification Key
            mf[5] = self.rkey.getenc128key() # MCERT Encryption Key
            self.mcert[15] = struct.pack(TCC_MF_FORMAT, *mf)
            self.mcert[8] = FACTORY_ENCRYPTION
            buf = bytearray(struct.pack(TCC_MCERT_FORMAT, *self.mcert))
            if self.pw:
                # Set IV
                mfiv = get_random_bytes(TCC_MCERT_IV_SIZE)
                # Set salt
                salt = get_random_bytes(TCC_MCERT_SALT_SIZE)
                # Set Key
                #key = pbkdf2_hmac('sha256', bytes(self.pw, 'utf-8'), salt, 1000, 16)
                temp = bytes(self.pw, 'utf-8')
                pad_size = MF_PASSWORD_LENGTH - (len(self.pw) % MF_PASSWORD_LENGTH)
                temp += bytearray(pad_size)
                temp += salt
                key = hashlib.sha256(temp).digest()
                out.write(buf[:TCC_MCERT_ENC_OFFSET] +
                        tcc_cbc_encrypt(key[:16], mfiv, buf[TCC_MCERT_ENC_OFFSET:-(TCC_MCERT_IV_SIZE + TCC_MCERT_SALT_SIZE)]))
                out.write(mfiv)
                out.write(salt)
            else:
                out.write(buf[:TCC_MCERT_ENC_OFFSET] + tccscram(buf[TCC_MCERT_ENC_OFFSET:]))
        elif self.enc:
            out.write(buf[:TCC_MCERT_ENC_OFFSET]
                    + tcc_encrypt(self.rkey.getenc128key(), buf[TCC_MCERT_ENC_OFFSET:], iv))
        else:
            out.write(buf)
        out.write(signature)

    def process(self, name):
        with open(name, "wb") as out:
            self.proc_mcert(out)

## verifier class
#
class verifier:
    def __init__(self, keybase=KEY_BASE):
        self.hkey = tcckeys(HKEY_NAME, keybase)
        self.rkey = tcckeys(RKEY_NAME, keybase)
        self.mkey = tcckeys(MKEY_NAME, keybase)

    def proc_mcert(self, f):
        buf = f.read(TCC_MCERT_ENC_OFFSET)
        mcert_iv = buf[TCC_MCERT_IV_OFFSET:TCC_MCERT_IV_OFFSET + TCC_MCERT_IV_SIZE]
        buf += tcc_decrypt(self.rkey.getenc128key(), f.read(TCC_MCERT_LENGTH - TCC_MCERT_ENC_OFFSET), mcert_iv)
        self.mcert = list(struct.unpack(TCC_MCERT_FORMAT, buf))
        signature = f.read()

        print("[MCERT]")
        print("  - Marker      : {}".format(self.mcert[0]))
        print("  - Format Ver  : {}".format(self.mcert[2]))
        print("  - Name        : {}".format(self.mcert[4]))
        print("  - ENC Option  : {}".format(self.mcert[8]))
        print("  - IV          : {}".format(binascii.hexlify(self.mcert[9])))
        print("  - Rollback ID : {}".format(self.mcert[10]))
        if self.mcert[8] == 0:
            res = True if self.mcert[12] == self.mkey.getverifykey() else False
            print("  - Pub Key     : {} ({})".format(binascii.hexlify(self.mcert[12]), res))
            res = True if self.mcert[13] == self.mkey.getenc128key() else False
            print("  - Enc Key     : {} ({})".format(binascii.hexlify(self.mcert[13]), res))
            res = tcc_verify(self.rkey.getverifykey(), buf, signature)
            print("  - Signature   : {} ({})".format(binascii.hexlify(signature), res))
        print("")

    def process(self, name):
        with open(name, "rb") as f:
            self.proc_mcert(f)

## Start Code
#
if (__name__ == "__main__"):
    parser = ArgumentParser(description="TCC MCERT Generation Tool")
    parser.add_argument("-k", "--keybase", type=str, default=KEY_BASE, \
            help="key directory")
    parser.add_argument("-o", "--output", type=str, \
            help="Output file name.")
    parser.add_argument("--no-enc", dest="enc", action="store_false", default=True, \
            help="Not encryption.")
    parser.add_argument("-f", "--factory", action="store_true", default=False, \
            help="Add information for secure boot migration.")
    parser.add_argument("-p", "--password", type=str, \
            help="input factory mode encryption password.(MAX 16 bytes)")
    parser.add_argument("-r", "--rbid", type=int, default=0, \
            help="Set ID for rollback protection.")
    parser.add_argument("-v", "--verify", type=str, \
            help="input file name for verification")
    args = parser.parse_args()

    if args.verify is None:
        signer(args.enc, args.rbid, args.factory, args.password, args.keybase).process(args.output)
    else:
        verifier(args.keybase).process(args.verify)
