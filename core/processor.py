import os

import cv2
import insightface
import core.globals
from core.config import get_face

FACE_SWAPPER = None


def get_face_swapper():
    global FACE_SWAPPER
    if FACE_SWAPPER is None:
        model_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../inswapper_128.onnx')
        FACE_SWAPPER = insightface.model_zoo.get_model(model_path, providers=core.globals.providers)
    return FACE_SWAPPER


def process_video(source_img, frame_paths):
    source_face = get_face(cv2.imread(source_img))
    for frame_path in frame_paths:
        frame = cv2.imread(frame_path)
        try:
            face = get_face(frame)
            if face:
                result = get_face_swapper().get(frame, face, source_face, paste_back=True)
                cv2.imwrite(frame_path, result)
                print('.', end='', flush=True)
            else:
                print('S', end='', flush=True)
        except Exception:
            print('E', end='', flush=True)
            pass


def process_img(source_img, target_path, output_file):
    frame = cv2.imread(target_path)
    face = get_face(frame)
    source_face = get_face(cv2.imread(source_img))
    result = get_face_swapper().get(frame, face, source_face, paste_back=True)
    cv2.imwrite(output_file, result)
    print("\n\nImage saved as:", output_file, "\n\n")
