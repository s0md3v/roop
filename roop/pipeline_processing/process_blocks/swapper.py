import os
from typing import Any

import onnxruntime
import cv2
import insightface

from ..common import Frame

from ..common import Frame
from ..environment import PipelineEnvironment
from ..process_blocks import ProcessBlock
from ..common import FaceAnalyser


class Swapper(ProcessBlock):
    """Swapper process block"""

    def __init__(self, environment: PipelineEnvironment) -> None:
        super().__init__(environment)
        self.analyser = FaceAnalyser(environment)

    def init(self, face: str) -> Any:
        self.face = self.analyser.get_face_single(cv2.imread(face))
        self.swapper = None

    def warmup(self) -> None:
        self.analyser.get_face_analyser()
        if not self.swapper:
            session_options = onnxruntime.SessionOptions()
            if self.environment.gpu_vendor is not None:
                session_options.intra_op_num_threads = self.environment.gpu_threads
            else:
                session_options.intra_op_num_threads = self.environment.cpu_threads
            session_options.execution_mode = onnxruntime.ExecutionMode.ORT_PARALLEL
            print(os.path.join(self.environment.models_path, 'inswapper_128.onnx'))
            model_path = os.path.join(self.environment.models_path, 'inswapper_128.onnx')
            self.swapper = insightface.model_zoo.get_model(model_path, providers=self.environment.providers, session_options=session_options)

    def process(self, frame: Frame) -> Any:
        if self.environment.all_faces:
            many_faces = self.analyser.get_face_many(frame.data)
            if many_faces:
                for face in many_faces:
                    frame.data = self.swapper.get(frame.data, face, self.face, paste_back=True)
        else:
            face = self.analyser.get_face_single(frame.data)
            if face:
                frame.data = self.swapper.get(frame.data, face, self.face, paste_back=True)

        return frame
    
    def release(self) -> None:
        pass