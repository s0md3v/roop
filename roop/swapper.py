import os
from tqdm import tqdm
import torch
import onnxruntime
import cv2
import insightface

import roop.globals
from roop.analyser import get_face_single, get_face_many

FACE_SWAPPER = None


def get_face_swapper():
    global FACE_SWAPPER
    if FACE_SWAPPER is None:
        session_options = onnxruntime.SessionOptions()
        if roop.globals.gpu_vendor is not None:
            session_options.intra_op_num_threads = roop.globals.gpu_threads
        else:
            session_options.intra_op_num_threads = roop.globals.cpu_threads
        session_options.execution_mode = onnxruntime.ExecutionMode.ORT_PARALLEL
        model_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../inswapper_128.onnx')
        FACE_SWAPPER = insightface.model_zoo.get_model(model_path, providers=roop.globals.providers, session_options=session_options)
    return FACE_SWAPPER


def swap_face_in_frame(source_face, target_face, frame):
    if target_face:
        return get_face_swapper().get(frame, target_face, source_face, paste_back=True)
    return frame


def process_faces(source_face, target_frame, progress):
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


def process_video(source_img, frame_paths):
    source_face = get_face_single(cv2.imread(source_img))
    progress_bar_format = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'

    with tqdm(total=len(frame_paths), desc="Processing", unit="frame", dynamic_ncols=True, bar_format=progress_bar_format) as progress:
        for frame_path in frame_paths:
            if roop.globals.gpu_vendor == 'nvidia':
                progress.set_postfix(cuda_utilization="{:02d}%".format(torch.cuda.utilization()), cuda_memory="{:02d}GB".format(torch.cuda.memory_usage()))
            frame = cv2.imread(frame_path)
            try:
                result = process_faces(source_face, frame, progress)
                cv2.imwrite(frame_path, result)
            except Exception:
                pass
            progress.update(1)


def process_img(source_img, target_path, output_file):
    frame = cv2.imread(target_path)
    face = get_face_single(frame)
    source_face = get_face_single(cv2.imread(source_img))
    result = get_face_swapper().get(frame, face, source_face, paste_back=True)
    cv2.imwrite(output_file, result)
    print("\n\nImage saved as:", output_file, "\n\n")
