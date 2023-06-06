
import os
from tqdm import tqdm
import cv2
import shutil
import insightface
import threading
import onnxruntime
import roop.globals
from roop.globals import providers
from roop.analyser import get_face_single, get_face_many
from roop.app import SCRFD_Child, ArcFaceONNX_Child

FACE_SWAPPER = None
THREAD_LOCK = threading.Lock()

class Facecheck:
    
    def __init__(self):
        model_dir = os.path.expanduser('~/.insightface/models/buffalo_l')
        detect_model_path =  os.path.join(model_dir, 'det_10g.onnx')
        feature_model_path = os.path.join(model_dir, 'w600k_r50.onnx')
        detect_session = onnxruntime.InferenceSession(detect_model_path, providers=providers)
        feature_session = onnxruntime.InferenceSession(feature_model_path, providers=providers)

        self.face_detector = SCRFD_Child(detect_model_path, detect_session)
        self.face_detector.prepare(0)

        self.feature_comparator = ArcFaceONNX_Child(feature_model_path, feature_session)
        self.feature_comparator.prepare(0)
    

    def get(self, swapped_face_path, framepaths, processing_paths):
        swapped_face = cv2.imread(swapped_face_path)
        swapped_face_boxes, swapped_face_keypoints = self.face_detector.autodetect(swapped_face)
        if swapped_face_boxes.shape[0] == 0:
            print("Face not found in swapped_face_image") 
        swapped_face_keypoint = swapped_face_keypoints[0]
        swapped_face_feature = self.feature_comparator.get(swapped_face, swapped_face_keypoint)
        for frame_path in framepaths:
            frame = cv2.imread(frame_path)
            try:
                boxes, keypoints = self.face_detector.autodetect(frame)
                keypoint = keypoints[0]
                face_feature = self.feature_comparator.get(frame, keypoint)
                similarity_level = self.feature_comparator.compute_sim(swapped_face_feature, face_feature)
                if similarity_level>=0.2:
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


def swap_face_in_frame(source_face, target_face, frame):
    if target_face:
        return get_face_swapper().get(frame, target_face, source_face, paste_back=True)
    return frame


def process_faces(source_face, target_frame):
    if roop.globals.all_faces:
        many_faces = get_face_many(target_frame)
        if many_faces:
            for face in many_faces:
                target_frame = swap_face_in_frame(source_face, face, target_frame)
    else:
        face = get_face_single(target_frame)
        if face:
            target_frame = swap_face_in_frame(source_face, face, target_frame)
    return target_frame


def process_frames(source_img, frame_paths, progress=None):
    source_face = get_face_single(cv2.imread(source_img))
    for frame_path in frame_paths:
        frame = cv2.imread(frame_path)
        try:
            result = process_faces(source_face, frame)
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
    source_face = get_face_single(cv2.imread(source_img))
    result = get_face_swapper().get(frame, face, source_face, paste_back=True)
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
