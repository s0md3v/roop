import onnxruntime

gpu = None
all_faces = False
log_level = 'error'
providers = onnxruntime.get_available_providers()

if 'TensorrtExecutionProvider' in providers:
    providers.remove('TensorrtExecutionProvider')
