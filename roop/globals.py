import onnxruntime
import os
from pathlib import Path

source_path = None
target_path = None
output_path = None
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
selective_face = None
selective_face_checkbox = None
log_level = 'error'
home = str(Path.home())
models = os.path.join(home, '.insightface/models/buffalo_l/')
comparator_model = os.path.join(models, 'w600k_r50.onnx')
providers = onnxruntime.get_available_providers()

if 'TensorrtExecutionProvider' in providers:
    providers.remove('TensorrtExecutionProvider')
