import insightface
import onnxruntime

from ..environment import PipelineEnvironment


class FaceAnalyser():
    """Face analyser"""
    def __init__(self, environment: PipelineEnvironment) -> None:
        self.environment = environment
        self.analyser = None

    def get_face_analyser(self):
        if self.analyser is None:
            session_options = onnxruntime.SessionOptions()
            if self.environment.gpu_vendor is not None:
                session_options.intra_op_num_threads = self.environment.gpu_threads
            else:
                session_options.intra_op_num_threads = self.environment.cpu_threads
            session_options.execution_mode = onnxruntime.ExecutionMode.ORT_PARALLEL
            self.analyser = insightface.app.FaceAnalysis(name='buffalo_l', providers=self.environment.providers)
            self.analyser.prepare(ctx_id=0, det_size=(640, 640))
        return self.analyser

    def get_face_single(self, img_data):
        face = self.get_face_analyser().get(img_data)
        try:
            return sorted(face, key=lambda x: x.bbox[0])[0]
        except IndexError:
            return None

    def get_face_many(self, img_data):
        try:
            return self.get_face_analyser().get(img_data)
        except IndexError:
            return None