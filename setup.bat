@echo off

REM Check if FFmpeg exists in PATH
where /q ffmpeg
IF ERRORLEVEL 1 (
    echo ffmpeg is missing. Ensure it is installed and placed in your PATH.
    echo https://ffmpeg.org/download.html
    pause
    EXIT /B
)

REM Check if Python exists in PATH
where /q python
IF ERRORLEVEL 1 (
    echo python is missing. Ensure it is installed and placed in your PATH.
    echo https://www.python.org/downloads/
    pause
    EXIT /B
)

IF NOT EXIST venv (
    python -m venv venv
) ELSE (
    echo venv folder already exists, skipping creation...
)
call .\venv\Scripts\activate.bat

echo Do you want to uninstall previous versions of torch and associated files before installing?
echo [1] - Yes
echo [2] - No (recommanded for most)
set /p uninstall_choice="Enter your choice (1 or 2): "

if %uninstall_choice%==1 (
    pip uninstall -y torch torchvision torchaudio
)

echo Please choose the version of torch you want to install:
echo [1] - CPU Only
echo [2] - NVIDIA CUDA 11.8 with cuDNN
set /p choice="Enter your choice (1 or 2): "



if %choice%==1 (
    pip install -r requirements.txt
)
if %choice%==2 (
    pip install -r requirements.txt
    pip uninstall -y onnxruntime onnxruntime-gpu
    pip uninstall -y torch torchvision torchaudio
    pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu118
    pip install onnxruntime-gpu
)

if not exist inswapper_128.onnx (
    echo Before run the application
    echo Please download "inswapper_128.onnx" from the installation instruction below and put it in roop root folder
    echo https://github.com/s0md3v/roop/wiki/1.-Installation
)

pause