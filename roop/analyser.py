from typing import Any
import insightface
import roop.globals
import onnxruntime

FACE_ANALYSER = None
FACE_COMPARATOR = None
session = None


def get_face_analyser() -> Any:
    global FACE_ANALYSER
    if FACE_ANALYSER is None:
        FACE_ANALYSER = insightface.app.FaceAnalysis(name='buffalo_l', providers=roop.globals.providers)
        FACE_ANALYSER.prepare(ctx_id=0, det_size=(640, 640))
    return FACE_ANALYSER


def get_face_comparator() -> Any:
    global FACE_COMPARATOR, session
    if FACE_COMPARATOR is None:
        if session is None:
            session = onnxruntime.InferenceSession(roop.globals.comparator_model, providers=['CUDAExecutionProvider'])
        FACE_COMPARATOR = insightface.model_zoo.arcface_onnx.ArcFaceONNX(model_file=roop.globals.comparator_model, session=session)
        FACE_COMPARATOR.prepare(ctx_id=0, det_size=(640, 640))
    return FACE_COMPARATOR


def get_one_face(image_data) -> Any:
    face = get_face_analyser().get(image_data)
    try:
        return min(face, key=lambda x: x.bbox[0])
    except ValueError:
        return None


def get_many_faces(image_data) -> Any:
    try:
        return get_face_analyser().get(image_data)
    except IndexError:
        return None


def get_face_filter(image_data):
    feat1 = roop.globals.selective_face
    likely_face = {
        "sim": 0,
        "face": None
    }
    so_likely_face = None
    for face in get_many_faces(image_data):
        feat2 = get_face_comparator().get(image_data, face)
        sim = get_face_comparator().compute_sim(feat1, feat2)
        if sim < 0.02:
            conclu = 'They are NOT the same person'
            continue
        elif 0.02 <= sim < 0.028:
            conclu = 'They are LIKELY TO be the same person'
            if likely_face['sim'] < sim:
                likely_face['sim'] = sim
                likely_face['face'] = face
            continue
        else:
            conclu = 'They ARE the same person'
            so_likely_face = face
            break
    if so_likely_face is None and likely_face['sim'] == 0:
        return None
    return so_likely_face if so_likely_face else likely_face
