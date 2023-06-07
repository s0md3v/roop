import onnxruntime

source_path = None
target_path = None
output_path = None
keep_fps = None
keep_audio = None
keep_frames = None
many_faces = None
video_encoder = None
video_quality = None
cpu_cores = None
gpu_threads = None
gpu_vendor = None
max_memory = None
headless = None
ffmpeg_encoder = None
log_level = 'error'
providers = onnxruntime.get_available_providers()

if 'TensorrtExecutionProvider' in providers:
    providers.remove('TensorrtExecutionProvider')

list_encoders = {
    'nvidia': 'h264_nvenc',
    'amd': 'h264_amf',
    'apple': 'h264_videotoolbox',
    'intel': 'h264_qsv'
}
