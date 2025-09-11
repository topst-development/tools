#!/usr/bin/env python3
import struct
import hashlib
import argparse

def make_tcc_image(rom, image, version, offset, target):
	# Certificate
	rom.write('CERT'.encode())
	rom.write(bytearray(252))

	# Header
	rom.write('HDR'.encode().ljust(4, b'\0'))     # MARKER
	rom.write(struct.pack("<L", len(image) + 128)) # Image and Appendix Length
	rom.write(struct.pack("<L", offset))           # Image Offset
	rom.write(bytearray(4))                        # Header Format Version
	rom.write('805x'.encode())                     # SoC Name
	rom.write('DCP'.encode().ljust(12, b'\0'))    # Image name
	rom.write(version.encode().ljust(16, b'\0'))  # Image version
	rom.write(struct.pack("<Q", target))           # Target Address
	rom.write(bytearray(40))
	rom.write(hashlib.sha256(image).digest())      # HASH
	rom.write(bytearray(128))                      # Reserved for SignTool
	if offset > 512:
		rom.write(bytearray(offset - 512))

	# Image
	rom.write(image)

	# Appendix
	rom.write(bytearray(128))

	return 0

def mkrom(romname, imagename, version, offset, target):
	image = open(imagename, 'rb')
	buf = image.read()
	length = (((len(buf) + 0x3F) >> 6) << 6)
	image.close()

	rom = open(romname, 'wb')
	make_tcc_image(rom, buf.ljust(length, b'\0'), version, offset, target)
	rom.close()
	return 0

parser = argparse.ArgumentParser(description='DCP image Generator')
parser.add_argument('-i', '--input', type=str, nargs=1, help='input file name')
parser.add_argument('-o', '--output', type=str, nargs=1, help='output file name')
args = parser.parse_args()

imageversion = '0.0.0'
imageoffset = 512
targetaddress = 0
iname = args.input[0]
oname = args.output[0]

mkrom(oname, iname, imageversion, imageoffset, targetaddress)

