import os
from tqdm import tqdm
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
    with tqdm(total=len(frame_paths), desc="Processing", unit="frame", dynamic_ncols=True, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]') as progress:
        for frame_path in frame_paths:
            frame = cv2.imread(frame_path)
            try:
                face = get_face(frame)
                if face:
                    result = get_face_swapper().get(frame, face, source_face, paste_back=True)
                    cv2.imwrite(frame_path, result)
                    progress.set_postfix(status='.', refresh=True)
                else:
                    progress.set_postfix(status='S', refresh=True)
            except Exception:
                progress.set_postfix(status='E', refresh=True)
                pass
            progress.update(1)


def process_img(source_img, target_path, output_file):
    frame = cv2.imread(target_path)
    face = get_face(frame)
    source_face = get_face(cv2.imread(source_img))
    result = get_face_swapper().get(frame, face, source_face, paste_back=True)
    cv2.imwrite(output_file, result)
    print("\n\nImage saved as:", output_file, "\n\n")
