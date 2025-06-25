# SNOR_IMAGE_MAKER v0.0

import argparse
import json
import math
import os.path
import io
from pathlib import Path, PureWindowsPath

def update_area(image, output, offset):
    image.seek(0, io.SEEK_END)
    print("image: %s offset: 0x%08X size: 0x%08X" % (image.name, offset, image.tell()))
    image.seek(0, io.SEEK_SET)

    # fill 0xFF to empty space
    cur_offset = output.tell()
    if cur_offset < offset:
        output.write(bytearray([0xFF] * (offset - cur_offset)))

    # write data
    data = image.read()
    output.seek(offset, 0)
    output.write(data)


parser = argparse.ArgumentParser(description='TCC750x SNOR Image Make Tool V.00')
parser.add_argument('-c', '--config',
                    required=False,
                    nargs=1,
                    default='tcc750x_snor.json',
                    type=str,
                    help='Configuration SNOR JSON File (default: tcc750x_snor.json)')
parser.add_argument('-o', '--output',
                    required=False,
                    nargs=1,
                    default='tcc750x_snor.rom',
                    type=str,
                    help='Output File Name (default: tcc750x_snor.rom)')

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
    area_data = json.load(json_file)

with open(out_file, "wb") as output_file:
    for img_data in area_data:
        for f_name in area_data[img_data]:
            file_windows_path = PureWindowsPath(f_name)
            file_path = Path(file_windows_path)
            priv_offset = 0
            with open(str(file_path), "rb") as img_file:
                offset = int(area_data[img_data][f_name][0]["addr"], 0) * 0x200
                update_area(img_file, output_file, offset)

    # add padding for 4KB alignment
    sector_size = 0x1000
    output_file.seek(0, io.SEEK_END)
    output_size = output_file.tell();
    sector_cnt = int((output_size + sector_size - 1) / sector_size)
    align_size = sector_cnt * sector_size
    if align_size > output_size:
        output_file.write(bytearray([0xFF] * (align_size - output_size)))
  
    print("Success! \nOutput: ", output_file.name)
