import os
import cv2
import glob
import numpy as np
import torch
import threading
from tqdm import tqdm
import roop.globals

from torchvision.transforms.functional import normalize

import codeformer.app as model
from codeformer.facelib.utils.face_restoration_helper import FaceRestoreHelper
from codeformer.basicsr.utils import img2tensor, tensor2img

FACE_HELPER = None
THREAD_LOCK = threading.Lock()


def get_face_enhancer():
    global FACE_HELPER
    with THREAD_LOCK:
        if FACE_HELPER == None:
            FACE_HELPER = FaceRestoreHelper(
            upscale_factor = int(2),
            face_size=512,
            crop_ratio=(1, 1),
            det_model="retinaface_resnet50",
            save_ext="png",
            use_parse=True,
            device=model.device,
        )
        return FACE_HELPER


def enhance_face_in_frame(frame: np.ndarray):
    try:
        preprocess_restore(frame)
        for idx, cropped_face in enumerate(get_face_enhancer().cropped_faces):
            face_t = data_preprocess(cropped_face)
            face_enhanced = restore_face(face_t)
            return face_enhanced
    except RuntimeError as error:
        print(f"Failed inference for CodeFormer: {error}")


def preprocess_restore(frame):
    get_face_enhancer().read_image(frame)
    # get face landmarks for each face
    get_face_enhancer().get_face_landmarks_5(
        only_center_face=False, resize=640, eye_dist_threshold=5
    )
    # align and warp each face
    get_face_enhancer().align_warp_face()


def data_preprocess(frame):
    frame_t = img2tensor(frame / 255.0, bgr2rgb=True, float32=True)
    normalize(frame_t, (0.5, 0.5, 0.5), (0.5, 0.5, 0.5), inplace=True)
    return frame_t.unsqueeze(0).to(model.device)


def generate_output(frame_t, codeformer_fidelity = 0.6):
    with torch.no_grad():
        output = model.codeformer_net(frame_t, w=codeformer_fidelity, adain=True)[0]
    return output


def postprocess_output(output):
    restored_face = tensor2img(output, rgb2bgr=True, min_max=(-1, 1))
    return restored_face.astype("uint8")


def restore_face(face_t):
    try:
        output = generate_output(face_t)
        restored_face = postprocess_output(output)
        del output
    except RuntimeError as error:
        print(f"Failed inference for CodeFormer: {error}")
        restored_face = postprocess_output(face_t)
    return restored_face


def paste_face_back(face_enhanced):
    get_face_enhancer().add_restored_face(face_enhanced)
    get_face_enhancer().get_inverse_affine()
    enhanced_img = get_face_enhancer().paste_faces_to_input_image()
    get_face_enhancer().clean_all()
    return enhanced_img




# def process_frames(frame_paths, codeformer_fidelity = 0.7):
#     total_frames = len(frame_paths)
#     progress_bar = tqdm(total=total_frames, desc="Processing Images", leave=True)
#     for frame_path in frame_paths:
#         img = cv2.imread(frame_path, cv2.IMREAD_COLOR)
#         enhanced_face = enhance_face_in_frame(img, codeformer_fidelity)
#         enhanced_img = paste_face_back(enhanced_face)
#         cv2.imwrite(frame_path, enhanced_img)
#         progress_bar.update(1)
#     progress_bar.close()


def process_frames(frame_paths, progress=None):
    # thread_id = threading.get_ident()
    # # acquire lock
    # lock = locks[thread_id]
    # lock.acquire()
    # # acquire resource
    # resource = resources[thread_id]
    # resource.extend(frame_paths)
    # # release lock
    # lock.release()

    for frame_path in frame_paths:
        frame = cv2.imread(frame_path, cv2.IMREAD_COLOR)
        try:
            enhanced_face = enhance_face_in_frame(frame)
            result = paste_face_back(enhanced_face)
            cv2.imwrite(frame_path, result)
            THREAD_LOCK.release()
        except Exception as exception:
            print(exception)
            pass
        if progress:
            progress.update(1)

# cannot use 
def multi_process_frame(frame_paths, num_threads, progress):
    threads = []
    resources = {}
    locks = {}
    num_frames_per_thread = len(frame_paths) // num_threads
    remaining_frames = len(frame_paths) % num_threads
    start_index = 0

    for i in range(num_threads):
        resources[i] = []
        locks[i] = THREAD_LOCK

    # create threads by frames
    for _ in range(num_threads):
        end_index = start_index + num_frames_per_thread
        if remaining_frames > 0:
            end_index += 1
            remaining_frames -= 1
        thread_frame_paths = frame_paths[start_index:end_index]
        thread = threading.Thread(target=process_frames, args=(locks, resources, thread_frame_paths, progress))
        threads.append(thread)
        thread.start()
        start_index = end_index
    # join threads
    for thread in threads:
        thread.join()


def process_image(target_path, output_file):
    frame = cv2.imread(target_path)
    enhanced_face = enhance_face_in_frame(frame)
    result = paste_face_back(enhanced_face)
    cv2.imwrite(output_file, result)
    THREAD_LOCK.release


def process_video(frame_paths, num_threads = 2):
    do_multi = roop.globals.gpu_vendor is not None and roop.globals.gpu_threads > 1
    total_frames = len(frame_paths)
    progress = tqdm(total=total_frames, desc="Enhance_frames", leave=True)
    with progress as progress:
        if do_multi:
            process_frames(frame_paths, progress)
            # multi_process_frame(frame_paths, num_threads, progress)
        else:
            process_frames(frame_paths, progress)

    






