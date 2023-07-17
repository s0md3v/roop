import threading
from typing import Any, Optional, List
import insightface
import numpy

import roop.globals
from roop.typing import Frame, Face

FACE_ANALYSER = None
THREAD_LOCK = threading.Lock()


def get_face_analyser() -> Any:
    global FACE_ANALYSER

    with THREAD_LOCK:
        if FACE_ANALYSER is None:
            FACE_ANALYSER = insightface.app.FaceAnalysis(name='buffalo_l', providers=roop.globals.execution_providers)
            FACE_ANALYSER.prepare(ctx_id=0)
    return FACE_ANALYSER


def clear_face_analyser() -> Any:
    global FACE_ANALYSER

    FACE_ANALYSER = None


def get_one_face(frame: Frame, position: int = 0) -> Optional[Face]:
    faces = get_many_faces(frame)
    if faces:
        try:
            return faces[position]
        except IndexError:
            return faces[-1]
    return None


def get_many_faces(frame: Frame) -> Optional[List[Face]]:
    try:
        return get_face_analyser().get(frame)
    except ValueError:
        return None


def find_similar_face(frame: Frame, reference_face: Face) -> Optional[Face]:
    faces = get_many_faces(frame)
    for face in faces:
        if hasattr(face, 'normed_embedding') and hasattr(reference_face, 'normed_embedding'):
            distance = numpy.sum(numpy.square(face.normed_embedding - reference_face.normed_embedding))
            if distance < roop.globals.similar_face_distance:
                return face
    return None
