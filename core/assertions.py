import os
import sys
import core
import torch
import shutil

def is_python_version_valid():
    if sys.version_info < (3, 9):
        quit('Python version is not supported - please upgrade to 3.9 or higher')

def is_ffmpeg_installed():
    if not shutil.which('ffmpeg'):
        quit('ffmpeg is not installed!')

def is_model_downloaded(root_path):
    model_path = os.path.join(root_path, 'inswapper_128.onnx')
    if not os.path.isfile(model_path):
        quit('File "inswapper_128.onnx" does not exist!')

def is_gpu_and_cuda_validated():
    if '--gpu' in sys.argv:
        NVIDIA_PROVIDERS = ['CUDAExecutionProvider', 'TensorrtExecutionProvider']
        if len(list(set(core.globals.providers) - set(NVIDIA_PROVIDERS))) == 1:
            CUDA_VERSION = torch.version.cuda
            CUDNN_VERSION = torch.backends.cudnn.version()
            if not torch.cuda.is_available() or not CUDA_VERSION:
                quit("You are using --gpu flag but CUDA isn't available or properly installed on your system.")
            if CUDA_VERSION > '11.8':
                quit(f"CUDA version {CUDA_VERSION} is not supported - please downgrade to 11.8")
            if CUDA_VERSION < '11.4':
                quit(f"CUDA version {CUDA_VERSION} is not supported - please upgrade to 11.8")
            if CUDNN_VERSION < 8220:
                quit(f"CUDNN version {CUDNN_VERSION} is not supported - please upgrade to 8.9.1")
            if CUDNN_VERSION > 8910:
                quit(f"CUDNN version {CUDNN_VERSION} is not supported - please downgrade to 8.9.1")
    else:
        core.globals.providers = ['CPUExecutionProvider']