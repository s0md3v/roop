from typing import Any
import insightface
import roop.globals
from roop.utilities import resolve_relative_path

FACE_ANALYSER = None


def get_face_analyser() -> Any:
    global FACE_ANALYSER

    if FACE_ANALYSER is None:
        FACE_ANALYSER = insightface.app.FaceAnalysis(
            name='buffalo_l',
            providers=roop.globals.execution_providers,
            root=resolve_relative_path('..') # not '../models' because insightface auto create 'models/'
            # url: https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip
        )
        FACE_ANALYSER.prepare(ctx_id=0, det_size=(640, 640))
    return FACE_ANALYSER


def get_one_face(frame: Any) -> Any:
    face = get_face_analyser().get(frame)
    try:
        return min(face, key=lambda x: x.bbox[0])
    except ValueError:
        return None


def get_many_faces(frame: Any) -> Any:
    try:
        return get_face_analyser().get(frame)
    except IndexError:
        return None
