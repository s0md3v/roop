import cv2
import insightface
import onnxruntime
import core.globals
from core.config import get_face
from core.utils import rreplace

face_swapper = insightface.model_zoo.get_model('inswapper_128.onnx', providers=core.globals.providers)


def process_video(source_img, frame_paths):
    source_face = get_face(cv2.imread(source_img))
    for frame_path in frame_paths:
        frame = cv2.imread(frame_path)
        try:
            face = get_face(frame)
            result = face_swapper.get(frame, face, source_face, paste_back=True)
            cv2.imwrite(frame_path, result)
        except Exception as e:
            pass


def process_img(source_img, target_path):
    frame = cv2.imread(target_path)
    face = get_face(frame)
    source_face = get_face(cv2.imread(source_img))
    result = face_swapper.get(frame, face, source_face, paste_back=True)
    target_path = rreplace(target_path, "/", "/swapped-", 1) if "/" in target_path else "swapped-"+target_path
    print(target_path)
    cv2.imwrite(target_path, result)
