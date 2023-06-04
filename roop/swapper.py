import os
from tqdm import tqdm
import torch
import onnxruntime
import cv2
import insightface
import threading
import roop.globals
from roop.analyser import get_face_single, get_face_many
from roop.globals import gpu_vendor

FACE_SWAPPER = None
lock = threading.Lock()

def get_face_swapper():
    global FACE_SWAPPER
    with lock:
        if FACE_SWAPPER is None:
            model_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../inswapper_128.onnx')
            FACE_SWAPPER = insightface.model_zoo.get_model(model_path, providers=roop.globals.providers)
    return FACE_SWAPPER


def swap_face_in_frame(source_face, target_face, frame):
    if target_face:
        return get_face_swapper().get(frame, target_face, source_face, paste_back=True)
    return frame


def process_frames(source_img, frame_paths, progress=None):
    source_face = get_face_single(cv2.imread(source_img))
    for frame_path in frame_paths:
        frame = cv2.imread(frame_path)
        try:
            result = process_faces(source_face, frame)
            cv2.imwrite(frame_path, result)
        except Exception as e:
            print(">>>>", e)
            pass
        if progress:
            progress.update(1)

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


def process_video(source_img, frame_paths, preview_callback):
    progress_bar_format = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'

    with tqdm(total=len(frame_paths), desc="Processing", unit="frame", dynamic_ncols=True, bar_format=progress_bar_format) as progress:
        # nvidia multi-threading
        if roop.globals.gpu_vendor == 'nvidia':
            #progress.set_postfix(cuda_utilization="{:02d}%".format(torch.cuda.utilization()), cuda_memory="{:02d}GB".format(torch.cuda.memory_usage()))
            # caculate the number of frames each threads processed
            num_threads = roop.globals.gpu_threads
            num_frames_per_thread = len(frame_paths) // num_threads
            remaining_frames = len(frame_paths) % num_threads
            # create thread list
            threads = []
            start_index = 0
            # create thread and launch
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
            for thread in threads:
                thread.join()
        else:
            process_frames(source_img, frame_paths, progress)


def process_img(source_img, target_path, output_file):
    frame = cv2.imread(target_path)
    face = get_face_single(frame)
    source_face = get_face_single(cv2.imread(source_img))
    result = get_face_swapper().get(frame, face, source_face, paste_back=True)
    cv2.imwrite(output_file, result)
    print("\n\nImage saved as:", output_file, "\n\n")
