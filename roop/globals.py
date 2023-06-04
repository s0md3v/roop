import onnxruntime

all_faces = None
log_level = 'error'
cpu_threads = None
gpu_threads = None
gpu_vendor = None
providers = onnxruntime.get_available_providers()

if 'TensorrtExecutionProvider' in providers:
    providers.remove('TensorrtExecutionProvider')
