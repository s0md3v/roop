import os.path 
import argparse
import cv2
from scrfd import SCRFD
from arcface_onnx import ArcFaceONNX

model_dir = os.path.expanduser('~/.insightface/models/buffalo_l')
detect_model_path =  os.path.join(model_dir, 'det_10g.onnx')
feature_model_path = os.path.join(model_dir, 'w600k_r50.onnx')

face_detector = SCRFD(detect_model_path)
face_detector.prepare(0)

feature_comparator = ArcFaceONNX(feature_model_path)
feature_comparator.prepare(0)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('img1', type=str)
    parser.add_argument('img2', type=str)
    return parser.parse_args()

def func(args):
    image1 = cv2.imread(args.img1)
    image2 = cv2.imread(args.img2)
    boxes1, kpss1 = face_detector.autodetect(image1, max_num=1)
    if boxes1.shape[0]==0:
        return -1.0, "Face not found in Image-1"
    boxes2, kpss2 = face_detector.autodetect(image2, max_num=1)
    if boxes2.shape[0]==0:
        return -1.0, "Face not found in Image-2"
    kps1 = kpss1[0]
    kps2 = kpss2[0]
    feat1 = feature_comparator.get(image1, kps1)
    feat2 = feature_comparator.get(image2, kps2)
    sim = feature_comparator.compute_sim(feat1, feat2)
    if sim<0.2:
        conclu = 'They are NOT the same person'
    elif sim>=0.2 and sim<0.28:
        conclu = 'They are LIKELY TO be the same person'
    else:
        conclu = 'They ARE the same person'
    return sim, conclu

if __name__ == '__main__':
    args = parse_args()
    output = func(args)
    print('sim: %.4f, message: %s'%(output[0], output[1]))