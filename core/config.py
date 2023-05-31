import insightface
import core.globals

face_analyser = insightface.app.FaceAnalysis(name='buffalo_l', providers=core.globals.providers)
face_analyser.prepare(ctx_id=0, det_size=(640, 640))


def get_face(img_data):
    analysed = face_analyser.get(img_data)
    try:
        return sorted(analysed, key=lambda x: x.bbox[0])[0]
    except IndexError:
        return None


def get_all_faces(img_data):
    analysed = face_analyser.get(img_data)
    try:
        return analysed
    except IndexError:
        return None
