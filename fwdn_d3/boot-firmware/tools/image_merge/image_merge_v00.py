import argparse
import json
import os.path
from pathlib import Path, PureWindowsPath

def update_area(image, output, offset):
    print("image: %s offset: 0x%08X" % (image.name, offset))
    data = image.read()
    output.seek(offset, 0)
    output.write(data)
    print("Update success")


parser = argparse.ArgumentParser(description='TCC805x Boot Firmware Image Merge Tool V.00')
parser.add_argument('-c', '--config',
                    required=False,
                    nargs=1,
                    default='tcc805x_boot.json',
                    type=str,
                    help='Configuration FWDN JSON File (default: tcc805x_boot0.json)')
parser.add_argument('-o', '--output',
                    required=False,
                    nargs=1,
                    default='tcc805x_boot.rom',
                    type=str,
                    help='Output File Name (default: tcc805x_boot0.rom)')

args = parser.parse_args()

if type(args.config) == list:
    config_file = args.config[0]
else:
    config_file = args.config

if type(args.output) == list:
    out_file = args.output[0]
else:
    out_file = args.output

with open(config_file, "r") as json_file:
    img_data = json.load(json_file)

with open(out_file, "wb") as output_file:
    for f_name in img_data:
        file_windows_path = PureWindowsPath(f_name)
        file_path = Path(file_windows_path)
        with open(str(file_path), "rb") as img_file:
            offset = int(img_data[f_name][0]["addr"], 0) * 0x200
            update_area(img_file, output_file, offset)
    print("Success!\nOutput: ", output_file.name)
