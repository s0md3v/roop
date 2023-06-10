import onnxruntime

source_path = None
target_path = None
output_path = None
frame_processors = None
keep_fps = None
keep_audio = None
keep_frames = None
many_faces = None
video_encoder = None
video_quality = None
max_memory = None
cpu_cores = None
gpu_threads = None
gpu_vendor = None
headless = None
log_level = 'error'
providers = onnxruntime.get_available_providers()

if 'TensorrtExecutionProvider' in providers:
    providers.remove('TensorrtExecutionProvider')
