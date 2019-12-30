@echo off
echo BAT directory is %~dp0
echo Current directory  is %CD%


pushd %~dp0

rmdir /Q /S ".\dist"

xcopy /y ".\server-mqtt.py" ".\dist\server-mqtt.py*"
xcopy /y ".\requirements.txt" ".\dist\requirements.txt*"
xcopy /y ".\modules" ".\dist\modules" /i /s
xcopy /y ".\config" ".\dist\config" /i /s
xcopy /y ".\logs" ".\dist\logs" /i /s
xcopy /y ".\rpi" ".\dist\rpi" /i /s

pause