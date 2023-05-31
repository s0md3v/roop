import os
import cv2
import insightface
import core.globals
from core.config import get_face
from core.utils import rreplace

if os.path.isfile('inswapper_128.onnx'):
    face_swapper = insightface.model_zoo.get_model('inswapper_128.onnx', providers=core.globals.providers)
else:
    quit('File "inswapper_128.onnx" does not exist!')


def process_video(source_img, frame_paths):
    source_face = get_face(cv2.imread(source_img))
    for frame_path in frame_paths:
        frame = cv2.imread(frame_path)
        try:
            if core.globals.all_faces:
                all_faces = get_all_faces(frame)
                result = frame
                for singleFace in all_faces:
                    if singleFace:
                        result = face_swapper.get(result, singleFace, source_face, paste_back=True)
                        print('.', end='', flush=True)
                    else:
                        print('S', end='', flush=True)
                if result is not None:
                    cv2.imwrite(frame_path, result)
            else:
                face = get_face(frame)
                if face:
                    result = face_swapper.get(frame, face, source_face, paste_back=True)
                    cv2.imwrite(frame_path, result)
                    print('.', end='', flush=True)
                else:
                    print('S', end='', flush=True)

        except Exception as e:
            print('E', end='', flush=True)
            pass


def process_img(source_img, target_path, output_file):
    frame = cv2.imread(target_path)
    face = get_face(frame)
    source_face = get_face(cv2.imread(source_img))
    result = face_swapper.get(frame, face, source_face, paste_back=True)
    cv2.imwrite(output_file, result)
    print("\n\nImage saved as:", output_file, "\n\n")
