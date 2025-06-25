#!/bin/bash

./fwdn --fwdn boot-firmware/fwdn.json
./fwdn --storage emmc --low-format
./fwdn -w boot-firmware/boot.##MODE##.json
./fwdn -w ##OUTPUT##.fai --storage emmc --area user
