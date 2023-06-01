import onnxruntime

use_gpu = False
providers = onnxruntime.get_available_providers()

if use_gpu and 'TensorrtExecutionProvider' in providers:
    providers.remove('TensorrtExecutionProvider')
