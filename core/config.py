import insightface

face_analyser = insightface.app.FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'ROCMExecutionProvider', 'CPUExecutionProvider'])
face_analyser.prepare(ctx_id=0, det_size=(640, 640))


def get_face(img_data):
    analysed = face_analyser.get(img_data)
    return sorted(analysed, key=lambda x: x.bbox[0])[0]
