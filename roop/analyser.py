from typing import Any
import insightface
import numpy

import roop.globals
import onnxruntime
from roop.scrfd import SCRFD
from roop.arcface_onnx import ArcFaceONNX
import os

FACE_ANALYSER = None
FACE_COMPARATOR = None
session = None
detector = SCRFD(os.path.join(roop.globals.models, 'det_10g.onnx'))
detector.prepare(0)
rec = ArcFaceONNX(roop.globals.comparator_model)
rec.prepare(0)


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
            onnxruntime.set_default_logger_severity(3)
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
    likely_person = None
    so_likely_person = None
    for face in get_many_faces(image_data):
        bbox = face['bbox'].astype(numpy.int)
        sim, _ = compare(roop.globals.selective_face, image_data[bbox[1]:bbox[3], bbox[0]:bbox[2]])
        if sim < 0.2:
            continue
        elif sim >= 0.2 and sim < 0.28:
            likely_person = face
        else:
            so_likely_person = face
            break
    return so_likely_person if so_likely_person is not None else likely_person


def compare(image1, image2):
    bboxes1, kpss1 = detector.autodetect(image1, max_num=1)
    if bboxes1.shape[0]==0:
        return -1.0, "Face not found in Image-1"
    bboxes2, kpss2 = detector.autodetect(image2, max_num=1)
    if bboxes2.shape[0]==0:
        return -1.0, "Face not found in Image-2"
    kps1 = kpss1[0]
    kps2 = kpss2[0]
    feat1 = rec.get(image1, kps1)
    feat2 = rec.get(image2, kps2)
    sim = rec.compute_sim(feat1, feat2)
    return sim, "Face found"


def get_feat(image):
    bboxes, kpss = detector.autodetect(image, max_num=1)
    if bboxes.shape[0] == 0:
        return -1.0, "Face not found in Image-1"
    kps = kpss[0]
    return rec.get(image, kps)
