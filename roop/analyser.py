import insightface
import onnxruntime
import roop.globals

FACE_ANALYSER = None


def get_face_analyser():
    global FACE_ANALYSER
    if FACE_ANALYSER is None:
        session_options = onnxruntime.SessionOptions()
        if roop.globals.gpu_vendor is not None:
            session_options.intra_op_num_threads = roop.globals.gpu_threads
        else:
            session_options.intra_op_num_threads = roop.globals.cpu_threads
        session_options.execution_mode = onnxruntime.ExecutionMode.ORT_PARALLEL
        FACE_ANALYSER = insightface.app.FaceAnalysis(name='buffalo_l', providers=roop.globals.providers)
        FACE_ANALYSER.prepare(ctx_id=0, det_size=(640, 640))
    return FACE_ANALYSER


def get_face_single(img_data):
    face = get_face_analyser().get(img_data)
    try:
        return sorted(face, key=lambda x: x.bbox[0])[0]
    except IndexError:
        return None


def get_face_many(img_data):
    try:
        return get_face_analyser().get(img_data)
    except IndexError:
        return None
