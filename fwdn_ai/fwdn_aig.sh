#!/bin/bash

echo TOPST AI-G FWDN Shell Script File

echo ""
lsusb | grep -i usb
read -p "Input USB Port number :" num
port_num=$num
echo ""

echo "Step 1. Connect between Host PC and TOPST AI-G"
./fwdn_aig --fwdn boot-firmware/tcc750x_fwdn.json --port "$port_num"

echo "Step 2. Low-format"
./fwdn_aig --storage emmc --low-format --port "$port_num"

echo "Step 3. Download boot-firmware"
./fwdn_aig -w boot-firmware/tcc750x_boot.json --port "$port_num"

echo "Step 4. Download FAI file (system image)"
./fwdn_aig -w output_aig.fai --storage emmc --area user --port "$port_num"

if [ $? -eq 0 ]; then
  echo "TOPST AI-G FWDN is complete!"
fi
