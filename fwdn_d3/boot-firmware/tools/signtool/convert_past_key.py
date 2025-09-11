
from ecdsa import SigningKey, VerifyingKey, NIST256p
import binascii
import os
import subprocess
from argparse import ArgumentParser, RawTextHelpFormatter

KEY_DIR = './keys'

SIGNKEY_NAME = "/signkey.pem"
ENCKEY_NAME = "/enckey.bin"

def impl_sign(past_key_file, start_offset, end_offset):
    return SigningKey.from_string(
        read_binary_range(past_key_file, start_offset, end_offset), curve=NIST256p)

def impl_verify(past_key_file, start_offset, end_offset):
    return VerifyingKey.from_string(
        read_binary_range(past_key_file, start_offset, end_offset), curve=NIST256p)

def get_keyname(past_key_file):
    return os.path.join(KEY_DIR , os.path.splitext(os.path.basename(past_key_file))[0] + "key")

def create_directories(past_key_file):
    if not os.path.exists(KEY_DIR):
        os.makedirs(KEY_DIR)
        print(" -", KEY_DIR)
    else:
        print(" - Directory already existed:", KEY_DIR)

    if past_key_file.endswith("root.key"):
        key_subdirs = ['hsmkey', 'rootkey']
    elif past_key_file.endswith("master.key"):
        key_subdirs = ['masterkey']
    elif past_key_file.endswith("image.key"):
        key_subdirs = ['imagekey']
    else:
        print(" - Error: Invalid key file specified.")
        return

    for subdir in key_subdirs:
        subdir_path = os.path.join(KEY_DIR, subdir)
        if not os.path.exists(subdir_path):
            os.makedirs(subdir_path)
            print(" -", "./" + os.path.relpath(subdir_path, start=os.getcwd()))
        else:
            print(" - Directory already existed:", "./" + os.path.relpath(subdir_path, start=os.getcwd()))

def read_binary_range(key_file, start_offset, end_offset):
    with open(key_file, 'rb') as file:
        file.seek(start_offset)
        enc_binary = file.read(end_offset - start_offset + 1)
    return enc_binary

def generate_encryption_key_binary(past_key_file):
    if past_key_file.endswith("root.key"):
        hsm_enc_binary = read_binary_range(past_key_file, 0xC0, 0xDF)
        root_enc_binary = read_binary_range(past_key_file, 0x50, 0x5F)
        hsm_out = get_keyname(past_key_file).replace("root", "hsm") + ENCKEY_NAME
        root_out = get_keyname(past_key_file) + ENCKEY_NAME

        with open(hsm_out, "wb") as hsm_file, open(root_out, "wb") as root_file:
            hsm_file.write(hsm_enc_binary)
            root_file.write(root_enc_binary)
        print(" -", hsm_out)
        print(" -", root_out)

    elif past_key_file.endswith(("master.key", "image.key")):
        enc_binary = read_binary_range(past_key_file, 0x50, 0x5F)
        out = get_keyname(past_key_file) + ENCKEY_NAME

        with open(out, "wb") as f:
            f.write(enc_binary)
        print(" -", out)
    else:
        raise ValueError("Invalid file path provided")


def generate_signkey(past_key_file):
    if past_key_file.endswith("root.key"):
        hsm_pri_key = impl_sign(past_key_file,0xE0, 0xFF)
        hsm_pub_key = impl_verify(past_key_file, 0x100, 0x13F)
        root_pri_key = impl_sign(past_key_file,0x60, 0x7F)
        root_pub_key = impl_verify(past_key_file, 0x80, 0xBF)
        hsm_out = get_keyname(past_key_file).replace("root", "hsm") + SIGNKEY_NAME
        root_out = get_keyname(past_key_file) + SIGNKEY_NAME

        subprocess.run(["openssl", "ecparam", "-name", "prime256v1", "-out", hsm_out], check=True)
        subprocess.run(["openssl", "ecparam", "-name", "prime256v1", "-out", root_out], check=True)

        with open(hsm_out, "ab") as hsm_file, open(root_out, "ab") as root_file:
            hsm_file.write(hsm_pri_key.to_pem())
            root_file.write(root_pri_key.to_pem())
        print(" -",hsm_out)
        print(" -",root_out)

    elif past_key_file.endswith(("master.key", "image.key")):
        pri_key = impl_sign(past_key_file, 0x60, 0x7F)
        pub_key = impl_verify(past_key_file, 0x80, 0xBF)
        out = get_keyname(past_key_file) + SIGNKEY_NAME

        subprocess.run(["openssl", "ecparam", "-name", "prime256v1", "-out", out], check=True)
    
        with open(out, "ab") as f:
            f.write(pri_key.to_pem())
        print(" -",out)

    else:
        raise ValueError("Invalid file path provided")


if (__name__ == "__main__"):
    parser = ArgumentParser(description="TCC Past key convert Tool", formatter_class=RawTextHelpFormatter)
    parser.add_argument("-i", "--input", type=str, help="Input past key file name.\n"
                                                         "past key list: [root.key] [master.key] [image.key]")
    args = parser.parse_args()

    if args.input.endswith(("root.key","master.key", "image.key")):
        print("\n[Create directories] (If a directory already exists, it does not create a directory.)")
        create_directories(args.input)
        
        print("\n[Generated encryption key binary]")
        generate_encryption_key_binary(args.input)

        print("\n[Generated signkey]")
        generate_signkey(args.input)
    else:
        parser.print_help()
