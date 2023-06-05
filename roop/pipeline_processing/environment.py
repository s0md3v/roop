import onnxruntime
import psutil


class PipelineEnvironment():
    """Pipeline process environment"""

    def __init__(self, models_path:  str) -> None:
        self.models_path = models_path
        self.all_faces = False
        self.log_level = 'error'
        self.cpu_threads = max(psutil.cpu_count() - 2, 2)
        self.gpu_threads = 8
        self.gpu_vendor = None
        self.providers = onnxruntime.get_available_providers()

        if 'TensorrtExecutionProvider' in self.providers:
            self.providers.remove('TensorrtExecutionProvider')