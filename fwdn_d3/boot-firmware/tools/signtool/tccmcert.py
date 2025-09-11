##
# TCC MCERT
#
import struct
import binascii
import hashlib
import os
from os import path
from argparse import ArgumentParser
from hashlib import sha256
from ecdsa import SigningKey, VerifyingKey, NIST256p
from Crypto.Cipher import AES
from tcckeys import tcckeys, KEY_BASE, HKEY_NAME, RKEY_NAME, MKEY_NAME, IKEY_NAME, RKEY_BASE
from tccscram import tccscram

TCC_MCERT_MARKER = b"MCERT"
TCC_MCERT_FORMAT = "<5s7sLB2sB12sBBBB24sL64s16s48s256s"
TCC_MCERT_LENGTH = struct.calcsize(TCC_MCERT_FORMAT)
TCC_MCERT_ENC_OFFSET = 64

TCC_MF_FORMAT = "<16s16s64s32s64s16s12s4s32s"
TCC_MF_LENGTH = struct.calcsize(TCC_MF_FORMAT)

FACTORY_ENCRYPTION = 0x80

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

def tcc_sign(keybuf, imgbuf):
    return impl_sign(imgbuf, keybuf)

def tcc_verify(keybuf, imgbuf, signature):
    return impl_verify(imgbuf, keybuf, signature)

def tcc_encrypt(keybuf, imgbuf):
    return impl_encrypt(imgbuf, reverse(keybuf))

def tcc_decrypt(keybuf, imgbuf):
    return impl_decrypt(imgbuf, reverse(keybuf))

def tcc_get_dirlists():
    filelists = os.listdir(RKEY_BASE)
    dirlists = [dir for dir in filelists if path.isdir(os.path.join(RKEY_BASE, dir))]
    dirlists.sort()
    return dirlists

def tcc_get_rpub_keytable():
    keytable = bytes(0)
    dirlists = tcc_get_dirlists()
    for dir in dirlists:
        keytable += tcckeys(dir, RKEY_BASE).getverifykey()
    return keytable

def tcc_get_rkey_enrpkr(key_idx):
    dirlists = tcc_get_dirlists()
    rkey_enrpkr = tcckeys(dirlists[key_idx], RKEY_BASE)
    return rkey_enrpkr
## signer class
#
class signer:
    def __init__(self, enc, rbid, fac, key_idx, enrpkr, keybase=KEY_BASE):
        self.fac = fac
        self.enc = enc
        self.rbid = rbid
        self.keyidx = key_idx
        self.enrpkr = enrpkr
        self.hkey = tcckeys(HKEY_NAME, keybase)
        self.rkey = tcckeys(RKEY_NAME, keybase)
        self.mkey = tcckeys(MKEY_NAME, keybase)
        self.mcert = list(struct.unpack(TCC_MCERT_FORMAT, bytearray(TCC_MCERT_LENGTH)))
        if self.enrpkr == False and self.keyidx != 0:
            print("[Warning] Set key_index to 0 automatically (rpkr is disabled)")
            self.keyidx = 0

    def proc_mcert(self, out):
        self.mcert[0] = TCC_MCERT_MARKER
        self.mcert[5] = self.keyidx
        self.mcert[12] = self.rbid
        self.mcert[13] = self.mkey.getverifykey()
        self.mcert[14] = self.mkey.getenc128key()
        buf = struct.pack(TCC_MCERT_FORMAT, *self.mcert)
        rkey_enrpkr = tcc_get_rkey_enrpkr(self.mcert[5])
        signature = tcc_sign(rkey_enrpkr.getsignkey(), buf)
        if self.fac:
            mf = list(struct.unpack(TCC_MF_FORMAT, bytearray(TCC_MF_LENGTH)))
            mf[2] = self.hkey.getverifykey() # HSM Verification Key
            mf[3] = self.hkey.getenc256key() # HSM Encryption Key
            if self.enrpkr == True :
                keytable = tcc_get_rpub_keytable()
                mf[4] = hashlib.sha256(keytable).digest()
                mf[4] += bytes(len(rkey_enrpkr.getverifykey()) - len(mf[4]))
            else:
                mf[4] = self.rkey.getverifykey() # MCERT Verification KeyA
            mf[5] = self.rkey.getenc128key() # MCERT Encryption Key
            self.mcert[16] = struct.pack(TCC_MF_FORMAT, *mf)
            self.mcert[10] = FACTORY_ENCRYPTION
            buf = bytearray(struct.pack(TCC_MCERT_FORMAT, *self.mcert))
            out.write(buf[:TCC_MCERT_ENC_OFFSET] + tccscram(buf[TCC_MCERT_ENC_OFFSET:]))
        elif self.enc:
            out.write(buf[:TCC_MCERT_ENC_OFFSET]
                    + tcc_encrypt(self.rkey.getenc128key(), buf[TCC_MCERT_ENC_OFFSET:]))
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
        buf = f.read(TCC_MCERT_ENC_OFFSET) + tcc_decrypt(self.rkey.getenc128key(), f.read(TCC_MCERT_LENGTH - TCC_MCERT_ENC_OFFSET))
        self.mcert = list(struct.unpack(TCC_MCERT_FORMAT, buf))
        signature = f.read()
        rkey_enrpkr = tcc_get_rkey_enrpkr(self.mcert[5])

        print("[MCERT]")
        print("  - Marker      : {}".format(self.mcert[0]))
        print("  - Format Ver  : {}".format(self.mcert[2]))
        print("  - Key Idx     : {}".format(self.mcert[5]))
        print("  - Name        : {}".format(self.mcert[6]))
        print("  - ENC Option  : {}".format(self.mcert[10]))
        print("  - Rollback ID : {}".format(self.mcert[12]))
        if self.mcert[10] == 0:
            res = True if self.mcert[13] == self.mkey.getverifykey() else False
            print("  - Pub Key     : {} ({})".format(binascii.hexlify(self.mcert[13]), res))
            res = True if self.mcert[14] == self.mkey.getenc128key() else False
            print("  - Enc Key     : {} ({})".format(binascii.hexlify(self.mcert[14]), res))
            res = tcc_verify(rkey_enrpkr.getverifykey(), buf, signature)
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
    parser.add_argument("-r", "--rbid", type=int, default=0, \
            help="Set ID for rollback protection.")
    parser.add_argument("-v", "--verify", type=str, \
            help="input file name for verification")
    parser.add_argument("-x", "--keyidx", type=int, default=0, \
            help="Number of Root public key.")
    parser.add_argument("--enrpkr", dest="enrpkr", action="store_true", default=False, \
            help="Enable root public key revocation.")
    args = parser.parse_args()

    if args.verify is None:
        signer(args.enc, args.rbid, args.factory, args.keyidx, args.enrpkr, args.keybase).process(args.output)
    else:
        verifier(args.keybase).process(args.verify)
