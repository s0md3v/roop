
import os
from tqdm import tqdm
import cv2
import shutil
import insightface
import threading
import roop.globals
from roop.analyser import get_face_single, get_face_many
from roop.scrfd import SCRFD
from roop.arcface_onnx import ArcFaceONNX

FACE_SWAPPER = None
THREAD_LOCK = threading.Lock()

class Facecheck:
    
    def __init__(self):
        model_dir = os.path.expanduser('~/.insightface/models/buffalo_l')
        detect_model_path =  os.path.join(model_dir, 'det_10g.onnx')
        feature_model_path = os.path.join(model_dir, 'w600k_r50.onnx')

        self.face_detector = SCRFD(detect_model_path)
        self.face_detector.prepare(0)

        self.feature_comparator = ArcFaceONNX(feature_model_path)
        self.feature_comparator.prepare(0)
    

    def get(self, fake_face_path, framepaths, processing_paths):
        fake_face = cv2.imread(fake_face_path)
        fake_face_boxes, fake_face_keypoints = self.face_detector.autodetect(fake_face)
        if fake_face_boxes.shape[0] == 0:
            print("Face not found in source_image") 
        fake_face_keypoint = fake_face_keypoints[0]
        fake_face_feature = self.feature_comparator.get(fake_face, fake_face_keypoint)
        for frame_path in framepaths:
            frame = cv2.imread(frame_path)
            try:
                boxes, keypoints = self.face_detector.autodetect(frame)
                keypoint = keypoints[0]
                face_feature = self.feature_comparator.get(frame, keypoint)
                similarity_level = self.feature_comparator.compute_sim(fake_face_feature, face_feature)
                if similarity_level>=0.25:
                    shutil.move(frame_path, processing_paths)
                else:
                    pass
            except:
                print("please select image within face")



def get_face_swapper():
    global FACE_SWAPPER
    with THREAD_LOCK:
        if FACE_SWAPPER is None:
            model_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../inswapper_128.onnx')
            FACE_SWAPPER = insightface.model_zoo.get_model(model_path, providers=roop.globals.providers)
    return FACE_SWAPPER


def swap_face_in_frame(fake_face, target_face, frame):
    if target_face:
        return get_face_swapper().get(frame, target_face, fake_face, paste_back=True)
    return frame


def process_faces(fake_face, target_frame):
    if roop.globals.all_faces:
        many_faces = get_face_many(target_frame)
        if many_faces:
            for face in many_faces:
                target_frame = swap_face_in_frame(fake_face, face, target_frame)
    else:
        face = get_face_single(target_frame)
        if face:
            target_frame = swap_face_in_frame(fake_face, face, target_frame)
    return target_frame


def process_frames(source_img, frame_paths, progress=None):
    fake_face = get_face_single(cv2.imread(source_img))
    for frame_path in frame_paths:
        frame = cv2.imread(frame_path)
        try:
            result = process_faces(fake_face, frame)
            cv2.imwrite(frame_path, result)
        except Exception as exception:
            print(exception)
            pass
        if progress:
            progress.update(1)


def multi_process_frame(source_img, frame_paths, progress):
    threads = []
    num_threads = roop.globals.gpu_threads
    num_frames_per_thread = len(frame_paths) // num_threads
    remaining_frames = len(frame_paths) % num_threads

    # create thread and launch
    start_index = 0
    for _ in range(num_threads):
        end_index = start_index + num_frames_per_thread
        if remaining_frames > 0:
            end_index += 1
            remaining_frames -= 1
        thread_frame_paths = frame_paths[start_index:end_index]
        thread = threading.Thread(target=process_frames, args=(source_img, thread_frame_paths, progress))
        threads.append(thread)
        thread.start()
        start_index = end_index

    # threading
    for thread in threads:
        thread.join()


def process_img(source_img, target_path, output_file):
    frame = cv2.imread(target_path)
    face = get_face_single(frame)
    fake_face = get_face_single(cv2.imread(source_img))
    result = get_face_swapper().get(frame, face, fake_face, paste_back=True)
    cv2.imwrite(output_file, result)
    print("\n\nImage saved as:", output_file, "\n\n")


def process_video(source_img, frame_paths):
    do_multi = roop.globals.gpu_vendor is not None and roop.globals.gpu_threads > 1
    progress_bar_format = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
    with tqdm(total=len(frame_paths), desc="Processing", unit="frame", dynamic_ncols=True, bar_format=progress_bar_format) as progress:
        if do_multi:
            multi_process_frame(source_img, frame_paths, progress)
        else:
            process_frames(source_img, frame_paths, progress)
