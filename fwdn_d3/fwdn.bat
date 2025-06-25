fwdn.exe --fwdn boot-firmware\fwdn.json
fwdn.exe --storage emmc --low-format
fwdn.exe -w boot-firmware\boot.##MODE##.json
fwdn.exe -w "##OUTPUT##.fai" --storage emmc --area user