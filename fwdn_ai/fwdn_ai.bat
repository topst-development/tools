@echo off
@REM TITLE FWDN_BATCH

:START
echo TOPST AI-G FWDN Batch File
@echo off
echo.
echo Find Port.
wmic path win32_pnpentity get caption /format:table| find "COM" 

:SET_PORT
echo.
set /p port_num=Input USB Port Number : 

if /i "%port_num%" == "" (
	goto SET_PORT
)

echo.
set FWDN_EXE=fwdn_ai.exe

echo.
echo Step 1. Connect between Host PC and TOPST AI-G 
%FWDN_EXE% --fwdn boot-firmware\tcc750x_fwdn.json --port %port_num%

echo.
echo Step 2. Low-format
%FWDN_EXE% --fwdn boot-firmware\tcc750x_fwdn.json --low-format --storage emmc --area user --port %port_num%

echo.
echo Step 3. Download boot-firmware
%FWDN_EXE% --fwdn boot-firmware\tcc750x_fwdn.json --write boot-firmware\tcc750x_boot.json --port %port_num%

echo.
echo Step 4. Download FAI file (system image)
%FWDN_EXE% --fwdn boot-firmware\tcc750x_fwdn.json --write output_aig.fai --storage emmc --area user --port %port_num%

echo.
echo TOPST AI-G FWDN is complete!
pause
cls
goto START

:NO
exit
