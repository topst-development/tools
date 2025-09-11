##
# TCC SECFW
#
import struct
import binascii
from argparse import ArgumentParser
from hashlib import sha256
from ecdsa import SigningKey, VerifyingKey, NIST256p
from Crypto.Cipher import AES
from tcckeys import tcckeys, KEY_BASE, MKEY_NAME, IKEY_NAME

TCCIMG_ALGINMENT_LENGTH = 64

TCCIMG_CERT_MARKER = b"CERT"
TCCIMG_CERT_FORMAT = "<4s8sL4s12s32s64s16s48s"
TCCIMG_CERT_LENGTH = struct.calcsize(TCCIMG_CERT_FORMAT)
TCCIMG_CERT_ENC_OFFSET = 64

TCCIMG_HEADER_MARKER = b"HDR\0"
TCCIMG_HEADER_FORMAT = "<4sLLL4s12s16sQL36s32sLLLLLL40s"
TCCIMG_HEADER_LENGTH = struct.calcsize(TCCIMG_HEADER_FORMAT)

TCCIMG_FOOTER_FORMAT = "<LLLLLLLLLLLLLLLL"
TCCIMG_FOOTER_LENGTH = struct.calcsize(TCCIMG_FOOTER_FORMAT)

TCCIMG_SIGNATURE_LENGTH = 64

ATTRIBUTE_TYPE_VERSION = 0x1
ATTRIBUTE_TYPE_RBID = 0x2
ATTRIBUTE_TYPE_CEID = 0x3
ATTRIBUTE_TYPE_IMGID = 0x4
ATTRIBUTE_TYPE_IMGSIZE = 0x5

# TCC805x-Specific
TCCIMG_IMAGES = dict()
TCCIMG_IMAGES[b"".ljust(12, b"\0")] = 0x0000
TCCIMG_IMAGES[b"DCP".ljust(12, b"\0")] = 0x3000
TCCIMG_IMAGES[b"A72-BL1".ljust(12, b"\0")] = 0x0272
TCCIMG_IMAGES[b"A72-BL2".ljust(12, b"\0")] = 0x3172
TCCIMG_IMAGES[b"A72-OPTEE".ljust(12, b"\0")] = 0x3272
TCCIMG_IMAGES[b"A72-BL3".ljust(12, b"\0")] = 0x3372
TCCIMG_IMAGES[b"A53-BL1".ljust(12, b"\0")] = 0x0253
TCCIMG_IMAGES[b"A53-BL2".ljust(12, b"\0")] = 0x3153
TCCIMG_IMAGES[b"A53-OPTEE".ljust(12, b"\0")] = 0x3253
TCCIMG_IMAGES[b"A53-BL3".ljust(12, b"\0")] = 0x3353
TCCIMG_IMAGES[b"FWDN-FW".ljust(12, b"\0")] = 0x01FF
TCCIMG_IMAGES[b"SC-FW".ljust(12, b"\0")] = 0x02D3
TCCIMG_IMAGES[b"R5-BL1".ljust(12, b"\0")] = 0x01FF
TCCIMG_IMAGES[b"R5-FW".ljust(12, b"\0")] = 0x02FF
TCCIMG_IMAGES[b"R5-SUB-FW".ljust(12, b"\0")] = 0x03FF

def impl_sign(imgbuf, keybuf):
    return SigningKey.from_string(
                keybuf, curve = NIST256p, hashfunc = sha256).sign(imgbuf)

def impl_verify(imgbuf, keybuf, signature):
    return VerifyingKey.from_string(
                keybuf, curve = NIST256p, hashfunc = sha256).verify(signature, imgbuf)

def impl_encrypt(imgbuf, enckey):
    tcciv = AES.new(enckey, AES.MODE_ECB).encrypt(struct.pack("<L", len(imgbuf)).rjust(16, b"\0"))
    return AES.new(enckey, AES.MODE_CBC, tcciv).encrypt(imgbuf)

def impl_decrypt(imgbuf, enckey):
    tcciv = AES.new(enckey, AES.MODE_ECB).encrypt(struct.pack("<L", len(imgbuf)).rjust(16, b"\0"))
    return AES.new(enckey, AES.MODE_CBC, tcciv).decrypt(imgbuf)

def reverse(strval):
    revval = type(strval)()
    if type(revval) == str:
        for i in range(len(strval),0,-1):
            revval += strval[i-1]
    else:
        for i in range(len(strval),0,-1):
            revval += bytes([strval[i-1]])
    return revval

def tcc_hash(imgbuf):
    return sha256(imgbuf).digest()

def tcc_sign(keybuf, imgbuf):
    return impl_sign(imgbuf, keybuf)

def tcc_verify(keybuf, imgbuf, signature):
    return impl_verify(imgbuf, keybuf, signature)

def tcc_encrypt(keybuf, imgbuf):
    return impl_encrypt(imgbuf, reverse(keybuf))

def tcc_decrypt(keybuf, imgbuf):
    return impl_decrypt(imgbuf, reverse(keybuf))

def getimageid(imagename):
    return TCCIMG_IMAGES[imagename]

def create_cert():
    cert = list(struct.unpack(TCCIMG_CERT_FORMAT, bytearray(TCCIMG_CERT_LENGTH)))
    cert[0] = TCCIMG_CERT_MARKER
    return cert

def create_header(imgbuf):
    header = list(struct.unpack(TCCIMG_HEADER_FORMAT, bytearray(TCCIMG_HEADER_LENGTH)))
    header[0] = TCCIMG_HEADER_MARKER
    header[1] = len(imgbuf) + TCCIMG_FOOTER_LENGTH + TCCIMG_SIGNATURE_LENGTH
    header[2] = TCCIMG_CERT_LENGTH + TCCIMG_HEADER_LENGTH
    header[10] = tcc_hash(imgbuf)
    return header

def create_footer(imgid, rbid, imglen):
    footer = list(struct.unpack(TCCIMG_FOOTER_FORMAT, bytearray(TCCIMG_FOOTER_LENGTH)))
    footer[0] = ATTRIBUTE_TYPE_VERSION
    footer[1] = 0x1
    footer[2] = ATTRIBUTE_TYPE_RBID
    footer[3] = rbid
    footer[4] = ATTRIBUTE_TYPE_CEID
    footer[5] = 0x0
    footer[6] = ATTRIBUTE_TYPE_IMGID
    footer[7] = imgid
    footer[8] = ATTRIBUTE_TYPE_IMGSIZE
    footer[9] = imglen
    return struct.pack(TCCIMG_FOOTER_FORMAT, *footer)

## signer class
#
class signer:
    def __init__(self, src, enc, rbid, keybase=KEY_BASE):
        self.enc = enc
        self.rbid = rbid
        self.mkey = tcckeys(MKEY_NAME, keybase)
        self.ikey = tcckeys(IKEY_NAME, keybase)
        with open(src, "rb") as f:
            self.cert = list(struct.unpack(TCCIMG_CERT_FORMAT, f.read(TCCIMG_CERT_LENGTH)))
            f.read(TCCIMG_SIGNATURE_LENGTH)
            self.header = list(struct.unpack(TCCIMG_HEADER_FORMAT, f.read(TCCIMG_HEADER_LENGTH)))
            f.read(TCCIMG_SIGNATURE_LENGTH)
            if self.cert[0] == TCCIMG_CERT_MARKER and self.header[0] == TCCIMG_HEADER_MARKER:
                f.seek(self.header[2])
                if self.header[1] > (TCCIMG_FOOTER_LENGTH + TCCIMG_SIGNATURE_LENGTH):
                    self.img_buf = f.read(self.header[1] - (TCCIMG_FOOTER_LENGTH + TCCIMG_SIGNATURE_LENGTH))
                else:
                    self.img_buf = None
                if getimageid(self.header[5]) == 0x02FF or getimageid(self.header[5]) == 0x03FF:
                    self.enc = False
            else:
                f.seek(0)
                self.img_buf = f.read()
                length = len(self.img_buf) % TCCIMG_ALGINMENT_LENGTH
                if length != 0:
                    self.img_buf += bytearray(TCCIMG_ALGINMENT_LENGTH - length)
                self.cert = create_cert()
                self.header = create_header(self.img_buf)

    def proc_cert(self, out):
        self.cert[6] = self.ikey.getverifykey()
        self.cert[7] = self.ikey.getenc128key()
        buf = struct.pack(TCCIMG_CERT_FORMAT, *self.cert)
        signature = tcc_sign(self.mkey.getsignkey(), buf)
        out.write(buf[:TCCIMG_CERT_ENC_OFFSET] + tcc_encrypt(self.mkey.getenc128key(), buf[TCCIMG_CERT_ENC_OFFSET:]))
        out.write(signature)

    def proc_hdr(self, out):
        self.header[10] = bytes(32) if self.img_buf is None else tcc_hash(self.img_buf)
        self.header[12] = getimageid(self.header[5])
        self.header[13] = self.rbid
        self.header[14] = 0 if self.img_buf is None else len(self.img_buf)
        self.header[15] = 1 if self.enc == True else 0
        signature = tcc_sign(self.ikey.getsignkey(), struct.pack(TCCIMG_HEADER_FORMAT, *self.header))
        out.write(struct.pack(TCCIMG_HEADER_FORMAT, *self.header))
        out.write(signature)

    def proc_body(self, out):
        footer = create_footer(self.header[12], self.header[13], self.header[14])
        signature = tcc_sign(self.ikey.getsignkey(), self.img_buf + footer)
        if self.header[2] > out.tell():
            out.write(bytearray(self.header[2] - out.tell()))
        if self.enc == True:
            out.write(tcc_encrypt(self.ikey.getenc128key(), self.img_buf))
        else:
            out.write(self.img_buf)
        out.write(footer)
        out.write(signature)

    def process(self, name):
        with open(name, "wb") as out:
            self.proc_cert(out)
            self.proc_hdr(out)
            if self.img_buf is not None:
                self.proc_body(out)

## verifier class
#
class verifier:
    def __init__(self, keybase=KEY_BASE):
        self.mkey = tcckeys(MKEY_NAME, keybase)
        self.ikey = tcckeys(IKEY_NAME, keybase)

    def proc_cert(self, f):
        buf = f.read(TCCIMG_CERT_ENC_OFFSET) + tcc_decrypt(self.mkey.getenc128key(), f.read(TCCIMG_CERT_LENGTH - TCCIMG_CERT_ENC_OFFSET))
        self.cert = list(struct.unpack(TCCIMG_CERT_FORMAT, buf))
        signature = f.read(TCCIMG_SIGNATURE_LENGTH)

        print("[TCC IMG (Cert Part)]")
        print("  - Marker      : {}".format(self.cert[0]))
        print("  - Format Ver  : {}".format(self.cert[2]))
        print("  - Name        : {}".format(self.cert[4]))
        res = True if self.cert[6] == self.ikey.getverifykey() else False
        print("  - Pub Key     : {} ({})".format(binascii.hexlify(self.cert[6]), res))
        res = True if self.cert[7] == self.ikey.getenc128key() else False
        print("  - Enc Key     : {} ({})".format(binascii.hexlify(self.cert[7]), res))
        res = tcc_verify(self.mkey.getverifykey(), buf, signature)
        print("  - Signature   : {} ({})".format(binascii.hexlify(signature), res))
        print("")

    def proc_hdr(self, f):
        buf = f.read(TCCIMG_HEADER_LENGTH)
        self.header = list(struct.unpack(TCCIMG_HEADER_FORMAT, buf))
        signature = f.read(TCCIMG_SIGNATURE_LENGTH)
        if self.header[2] > 0x200:
            f.seek(self.header[2])
        if self.header[15] == 0:
            self.img = f.read(self.header[14])
        else:
            self.img = tcc_decrypt(self.ikey.getenc128key(), f.read(self.header[14]))

        print("[TCC IMG (HDR Part)]")
        print("  - Marker      : {}".format(self.header[0]))
        print("  - Body Size   : {} bytes".format(self.header[1]))
        print("  - Body Offset : {}".format(hex(self.header[2])))
        print("  - Format Ver  : {}".format(self.header[3]))
        print("  - SoC Name    : {}".format(self.header[4]))
        print("  - Image Name  : {}".format(self.header[5]))
        print("  - Image Ver   : {}".format(self.header[6]))
        print("  - Target Addr : {}".format(hex(self.header[7])))
        print("  - Exec State  : {}".format(hex(self.header[8])))
        res = True if tcc_hash(self.img) == self.header[10] else False
        print("  - Body Hash   : {} ({})".format(binascii.hexlify(self.header[10]), res))
        print("  - Image ID    : {}".format(hex(self.header[12])))
        print("  - Rollback ID : {}".format(self.header[13]))
        print("  - Binary Size : {} bytes".format(self.header[14]))
        print("  - Encryption  : {}".format(self.header[15]))
        res = tcc_verify(self.ikey.getverifykey(), buf, signature)
        print("  - Signature   : {} ({})".format(binascii.hexlify(signature), res))
        print("")

    def proc_body(self, f):
        buf = f.read(64)
        self.footer = list(struct.unpack(TCCIMG_FOOTER_FORMAT, buf))
        signature = f.read(64)

        print("[TCC IMG (Body Part)]")
        res = True if self.footer[0] == ATTRIBUTE_TYPE_VERSION else False
        print("  - Format Ver  : {} ({})".format(self.footer[1], res))
        res = True if self.footer[2] == ATTRIBUTE_TYPE_RBID else False
        print("  - Rollback ID : {} ({})".format(self.footer[3], res))
        res = True if self.footer[4] == ATTRIBUTE_TYPE_CEID else False
        print("  - Marker ID   : {} ({})".format(self.footer[5], res))
        res = True if self.footer[6] == ATTRIBUTE_TYPE_IMGID else False
        print("  - Image ID    : {} ({})".format(hex(self.footer[7]), res))
        res = True if self.footer[8] == ATTRIBUTE_TYPE_IMGSIZE else False
        print("  - Binary Size : {} bytes".format(self.footer[9], res))
        res = tcc_verify(self.ikey.getverifykey(), self.img + buf, signature)
        print("  - Signature   : {} ({})".format(binascii.hexlify(signature), res))
        print("")

    def process(self, name):
        with open(name, "rb") as f:
            self.proc_cert(f)
            self.proc_hdr(f)
            self.proc_body(f)

## Start Code
#
if (__name__ == "__main__"):
    parser = ArgumentParser(description="TCC F/W Sign Tool")
    parser.add_argument("-k", "--keybase", type=str, default=KEY_BASE, \
            help="keys directory")
    parser.add_argument("-i", "--input", type=str, \
            help="input file name")
    parser.add_argument("-o", "--output", type=str, \
            help="output file name (Default: [input file name].secure)")
    parser.add_argument("-e", "--enc", action="store_true", default=False, \
            help="encryption")
    parser.add_argument("-r", "--rbid", type=int, default=0, \
            help="rollback protection id")
    parser.add_argument("-v", "--verify", type=str, \
            help="input file name for verification")
    args = parser.parse_args()

    if args.verify is None:
        if args.output is None:
            args.output = args.input + ".secure"
        signer(args.input, args.enc, args.rbid, args.keybase).process(args.output)
    else:
        verifier(args.keybase).process(args.verify)
