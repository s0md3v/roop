import torch
import onnxruntime

use_gpu = False
providers = onnxruntime.get_available_providers()

if 'TensorrtExecutionProvider' in providers:
    providers.remove('TensorrtExecutionProvider')
