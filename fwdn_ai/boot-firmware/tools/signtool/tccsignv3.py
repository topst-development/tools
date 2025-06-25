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

def process_file(file_path, file_data_list,fac, found):
    name = file_path if isinstance(file_data_list, list) else file_data_list
    name = os.path.join(*name.replace("..\\..\\", "").split("\\"))
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
    
    if isinstance(file_data_list, list):
        return file_path + exname, file_data_list, found
    else:
        return file_path, file_data_list + exname , found

def process_nested_dict(json_dict, fac, found):
    new_dict = {}
    for key, val in json_dict.items():
        if isinstance(val, dict):
            print(f" {key}")
            val, found = process_nested_dict(val, fac, found)
        else:
            file_path, val, found = process_file(key, val, fac, found)
            key = file_path
        new_dict[key] = val
    return new_dict, found


def json_run(input, fac):
    file = open(input)
    jsonString = json.load(file)
    dic = dict()
    prefixname = FACNAME + "-" if fac else SECNAME + "-"
    output = os.path.join(os.path.dirname(input), prefixname + os.path.basename(input))

    print("[GENERATING] " + output)

    found = False
    ftype = False
    
    for key, val in jsonString.items():
        if isinstance(val, dict): #if json for snor
            print(f" {key}")
            ftype = True
            val, found = process_nested_dict(val, fac, found)
            dic[key] = val
            print("")
        else :
            key, val, found = process_file(key, val, fac, found)
            dic[key] = val
    print("")
    if found:
        with open(output, "w") as outfile:
            json.dump(dic, outfile, indent=4)
    if ftype:
        snor.append(os.path.abspath(output))


def cfg_run(input, fac):
    file = open(input, "r")
    newline = str()
    lines = file.readlines()
    exname = "." + FACNAME if fac else "." + SECNAME
    prefixname = FACNAME + "-" if fac else SECNAME + "-"
    output = os.path.join(os.path.dirname(input), prefixname + os.path.basename(input))

    print("[GENERATING] " + output)

    # TCC750x-Specific
    secfwnames = [ "DRAM_PARAM", "BL1_BIN", "BL2_BIN", "BL3_BIN" ]

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
            if not found:
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
                cfg_run(input=src, fac=False)
                cfg_run(input=src, fac=True)


    for rom in list(set(secfw)):
        out = rom + "." + SECNAME
        #print(out)
        tccsecfw.signer(src=rom, enc=args.enc, rbid=args.rbid).process(out)

    for rom in list(set(hsmfw)):
        out = rom + "." + SECNAME
        #print(out)
        ssshsm.signer(src=rom, rbid=args.rbid, fac=False, pw="password").process(out)
        out = rom + "." + FACNAME
        #print(out)
        ssshsm.signer(src=rom, rbid=args.rbid, fac=True, pw="password").process(out)

    for rom in list(set(mcert)):
        out = rom + "." + SECNAME
        #print(out)
        tccmcert.signer(enc=True, rbid=args.rbid, fac=False, pw="password").process(out)
        out = rom + "." + FACNAME
        #print(out)
        tccmcert.signer(enc=True, rbid=args.rbid, fac=True, pw="password").process(out)

    for rom in list(set(snor)):
        dirname = os.path.dirname(rom)
        out = os.path.splitext(os.path.basename(rom))[0] + ".rom"
        DEVNULL = open(os.devnull, 'wb')

        if 'snor_mkimage' in dirname:
            subprocess.call("./snor_mkimage -i " + os.path.basename(rom) + " -o " + out,
                        cwd=os.path.dirname(rom), shell=True, stdout=DEVNULL)
        elif 'snor_image_maker' in dirname:
            base_path = "./tools/snor_image_maker/"
            files = os.listdir(base_path)
            scripts = [f for f in files if f.startswith("snor_image_maker") and f.endswith(".py")]

            if len(scripts) == 1:
                subprocess.call("python3 " + base_path + scripts[0] + " -c " +
                os.path.join(base_path , os.path.basename(rom)) + " -o " +
                os.path.join(base_path ,out),
                cwd=os.path.join(os.path.dirname(rom), "../../"), shell=True, stdout=DEVNULL)
            else:
                print("Unable to find .py files starting with snor_image_maker.\n"
                "Otherwise Multiple .py files starting with snor_image_maker have been found.")
            
        else:
            continue