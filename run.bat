@echo off

if not exist inswapper_128.onnx (
    echo Before run the application
    echo Please download "inswapper_128.onnx" from the installation instruction below and put it in roop root folder
    echo https://github.com/s0md3v/roop/wiki/1.-Installation
    EXIT /B
)

:: Activate the virtual environment
call .\venv\Scripts\activate.bat
set PATH=%PATH%;%~dp0venv\Lib\site-packages\torch\lib

:: If the exit code is 0, run the run.py script with the command-line arguments
if %errorlevel% equ 0 (
    python.exe run.py %*
)