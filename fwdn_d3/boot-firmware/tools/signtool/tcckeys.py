##
# TCC Keys
#
from os import path
from ecdsa import SigningKey, NIST256p

RKEY_NAME = "rootkey"
HKEY_NAME = "hsmkey"
MKEY_NAME = "masterkey"
IKEY_NAME = "imagekey"

SIGNKEY_NAME = "signkey.pem"
ENCKEY_NAME = "enckey.bin"

KEY_BASE = path.join(path.dirname(path.realpath(__file__)), "keys")
RKEY_BASE = path.join(KEY_BASE, RKEY_NAME)

## tcckeys class
#
class tcckeys:
    def __init__(self, keyname, keybase=KEY_BASE):
        keydir = path.join(keybase, keyname)
        if path.isdir(keydir):
            with open(path.join(keydir, SIGNKEY_NAME), "rb") as src:
                self.sk = SigningKey.from_pem(src.read())
            if path.basename(keybase) != RKEY_NAME:
                with open(path.join(keydir, ENCKEY_NAME), "rb") as src:
                    self.ek = src.read()
        else:
            print("[ERR] {} is not directory".format(keydir))

    def getenc256key(self):
        if len(self.ek) == 32:
            return self.ek
        return None

    def getenc128key(self):
        if len(self.ek) == 16:
            return self.ek
        return None

    def getsignkey(self):
        return self.sk.to_string()

    def getverifykey(self):
        return self.sk.get_verifying_key().to_string()
