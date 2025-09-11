##
# TCC Sign
#
import os
import json
import struct
import subprocess
import ssshsm
import tccmcert
import tccsecfw
from argparse import ArgumentParser

FACNAME = "factory"
SECNAME = "secure"

secfw = list()
mcert = list()
hsmfw = list()
snor = list()

def json_run(input, fac):
    file = open(input)
    jsonString = json.load(file)
    dic = dict()
    prefixname = FACNAME + "-" if fac else SECNAME + "-"
    output = os.path.join(os.path.dirname(input), prefixname + os.path.basename(input))

    print("[GENERATING] " + output)

    found = False
    for key, val in jsonString.items():
        name = key if type(val) == list else val
        name = os.path.join(os.path.dirname(input), *name.replace(".\\", "").split("\\"))
        exname = ""
        if os.path.isfile(name):
            with open(name, "rb") as f:
                buf = f.read(16)
                if buf[:4] == b"CERT":
                    secfw.append(os.path.abspath(name))
                    exname = "." + SECNAME
                    print(" - " + os.path.relpath(name) + exname)
                    found = True
                elif buf[:5] == b"MCERT":
                    mcert.append(os.path.abspath(name))
                    exname = "." + FACNAME if fac else "." + SECNAME
                    print(" - " + os.path.relpath(name) + exname)
                    found = True
                else:
                    hdr = struct.unpack("<LLLL", buf)
                    if hdr[0] == 0 and ((hdr[2] * 4) + 160) == hdr[3]:
                        exname = "." + FACNAME if fac else "." + SECNAME
                        hsmfw.append(os.path.abspath(name))
                        print(" - " + os.path.relpath(name) + exname)
                        found = True
                    else:
                        print(" - " + os.path.relpath(name))
        if type(val) == list:
            dic[key + exname] = val
        else:
            dic[key] = val + exname

    print("")

    if found:
        with open(output, "w") as outfile:
            json.dump(dic, outfile, indent=4)

def snor_run(input, fac):
    file = open(input, "r")
    newline = str()
    lines = file.readlines()
    exname = "." + FACNAME if fac else "." + SECNAME
    prefixname = FACNAME + "-" if fac else SECNAME + "-"
    output = os.path.join(os.path.dirname(input), prefixname + os.path.basename(input))

    print("[GENERATING] " + output)

    # TCC805x-Specific
    secfwnames = [ "R5BL1_BIN", "MICOM_BIN", "UPDATE_BIN" ]

    for line in lines:
        if line.find("MCERT_BIN=") == 0:
            t = line.split("=")
            t = os.path.join(os.path.dirname(input), t[1].replace("\n", ""))
            mcert.append(os.path.abspath(t))
            print(" - " + os.path.relpath(t) + exname)
            newline += line.replace("\n", "") + exname + "\n"
        elif line.find("HSM_BIN=") == 0:
            t = line.split("=")
            t = os.path.join(os.path.dirname(input), t[1].replace("\n", ""))
            hsmfw.append(os.path.abspath(t))
            print(" - " + os.path.relpath(t) + exname)
            newline += line.replace("\n", "") + exname + "\n"
        else:
            found = False
            for name in secfwnames:
                if line.find(name + "=") == 0:
                    t = line.split("=")
                    t = os.path.join(os.path.dirname(input), t[1].replace("\n", ""))
                    secfw.append(os.path.abspath(t))
                    print(" - " + os.path.relpath(t) + ".secure")
                    newline += line.replace("\n", "") + ".secure" + "\n"
                    found = True
                    break
            if found == False:
                newline += line

    print("")

    file = open(output, "w")
    file.writelines(newline)
    file.close()
    snor.append(os.path.abspath(output))

## Start Code
#
if (__name__ == "__main__"):
    parser = ArgumentParser(description="TCC JSON TOOL v3")
    parser.add_argument("-i", "--input", type=str, nargs="+", \
            help="input file name")
    parser.add_argument("-e", "--enc", action="store_true", default=False, \
            help="encryption")
    parser.add_argument("-r", "--rbid", type=int, default=0, \
            help="rollback protection id")
    parser.add_argument("-x", "--keyidx", type=int, default=0, \
            help="Number of Root public key.")
    parser.add_argument("--enrpkr", dest="enrpkr", action="store_true", default=False, \
            help="Enable root public key revocation.")
    args = parser.parse_args()

    for src in args.input:
        if os.path.splitext(src)[1] == ".json":
            prefixname = os.path.basename(src).split("-")[0]
            if prefixname != FACNAME and prefixname != SECNAME:
                json_run(input=src, fac=False)
                json_run(input=src, fac=True)
        elif os.path.splitext(src)[1] == ".cfg":
            prefixname = os.path.basename(src).split("-")[0]
            if prefixname != FACNAME and prefixname != SECNAME:
                snor_run(input=src, fac=False)
                snor_run(input=src, fac=True)

    for rom in list(set(secfw)):
        out = rom + "." + SECNAME
        #print(out)
        tccsecfw.signer(src=rom, enc=args.enc, rbid=args.rbid).process(out)

    for rom in list(set(hsmfw)):
        out = rom + "." + SECNAME
        #print(out)
        ssshsm.signer(src=rom, rbid=args.rbid, fac=False).process(out)
        out = rom + "." + FACNAME
        #print(out)
        ssshsm.signer(src=rom, rbid=args.rbid, fac=True).process(out)

    for rom in list(set(mcert)):
        out = rom + "." + SECNAME
        #print(out)
        tccmcert.signer(enc=True, rbid=args.rbid, fac=False, key_idx=args.keyidx, enrpkr=args.enrpkr).process(out)
        out = rom + "." + FACNAME
        #print(out)
        tccmcert.signer(enc=True, rbid=args.rbid, fac=True, key_idx=args.keyidx, enrpkr=args.enrpkr).process(out)

    for rom in list(set(snor)):
        out = os.path.splitext(os.path.basename(rom))[0] + ".rom"
        #print(os.path.join(os.path.dirname(rom), out))
        DEVNULL = open(os.devnull, 'wb')
        subprocess.call("./tcc805x-snor-mkimage -i " + os.path.basename(rom) + " -o " \
                + out, cwd=os.path.dirname(rom), shell=True, stdout=DEVNULL)
