import os
import cv2
import insightface
import core.globals
from core.config import get_face
FACE_SWAPPER = None


def get_face_swapper():
    global FACE_SWAPPER
    if FACE_SWAPPER is None:
        FACE_SWAPPER = insightface.model_zoo.get_model(os.path.join(os.path.abspath(os.path.dirname(__file__)), '../inswapper_128.onnx'), providers=core.globals.providers)
    return FACE_SWAPPER


def process_video(source_img, frame_paths):
    source_face = get_face(cv2.imread(source_img))
    for frame_path in frame_paths:
        frame = cv2.imread(frame_path)
        try:
            face = get_face(frame)
            if face:
                cv2.imwrite(frame_path, get_face_swapper().get(frame, face, source_face, paste_back=True))
                print('.', end='', flush=True)
            else:
                print('S', end='', flush=True)
        except:
            print('E', end='', flush=True)


def process_img(source_img, target_path, output_file):
    frame = cv2.imread(target_path)
    cv2.imwrite(output_file, get_face_swapper().get(frame, get_face(frame), get_face(cv2.imread(source_img)), paste_back=True))
    print("\n\nImage saved as:", output_file, "\n\n")
