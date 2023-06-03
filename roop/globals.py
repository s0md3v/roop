import onnxruntime
import psutil

all_faces = False
log_level = 'error'
cpu_threads = max(psutil.cpu_count() - 2, 2)
gpu_threads = 8
gpu_vendor = None
providers = onnxruntime.get_available_providers()

if 'TensorrtExecutionProvider' in providers:
    providers.remove('TensorrtExecutionProvider')
