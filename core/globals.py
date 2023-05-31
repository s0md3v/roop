import onnxruntime

use_gpu = False
providers = onnxruntime.get_available_providers()
all_faces = False

if 'TensorrtExecutionProvider' in providers:
    providers.remove('TensorrtExecutionProvider')
