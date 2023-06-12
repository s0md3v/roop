from typing import Any, List
from tqdm import tqdm
import cv2
import insightface
import threading

import roop.globals
from roop.analyser import get_one_face, get_many_faces
from roop.utilities import conditional_download, resolve_relative_path

FACE_SWAPPER = None
THREAD_LOCK = threading.Lock()
FRAME_COUNTER = 0


def pre_check() -> None:
    download_directory_path = resolve_relative_path('../models')
    conditional_download(download_directory_path, ['https://huggingface.co/deepinsight/inswapper/resolve/main/inswapper_128.onnx'])


def get_face_swapper() -> None:
    global FACE_SWAPPER

    with THREAD_LOCK:
        if FACE_SWAPPER is None:
            model_path = resolve_relative_path('../models/inswapper_128.onnx')
            FACE_SWAPPER = insightface.model_zoo.get_model(model_path, providers=roop.globals.providers)
    return FACE_SWAPPER


def swap_face(source_face: Any, target_face: Any, temp_frame: Any) -> Any:
    if target_face:
        return get_face_swapper().get(temp_frame, target_face, source_face, paste_back=True)
    return temp_frame


def process_faces(source_face: Any, temp_frame: Any) -> Any:
    if roop.globals.many_faces:
        many_faces = get_many_faces(temp_frame)
        if many_faces:
            for target_face in many_faces:
                temp_frame = swap_face(source_face, target_face, temp_frame)
    else:
        target_face = get_one_face(temp_frame)
        if target_face:
            temp_frame = swap_face(source_face, target_face, temp_frame)
    return temp_frame


def process_frames(source_path: str, temp_frame_paths: List[str], progress=None) -> None:
    global FRAME_COUNTER
    total_frames = len(temp_frame_paths)
    source_face = get_one_face(cv2.imread(source_path))
    while True:
        with THREAD_LOCK:
            if FRAME_COUNTER >= total_frames:
                break
            temp_frame_path = temp_frame_paths[FRAME_COUNTER]
            FRAME_COUNTER += 1
        temp_frame = cv2.imread(temp_frame_path)
        try:
            result = process_faces(source_face, temp_frame)
            cv2.imwrite(temp_frame_path, result)
        except Exception as exception:
            print(exception)
            pass
        if progress:
            progress.update(1)


def multi_process_frame(source_path: str, temp_frame_paths: List[str], progress) -> None:
    threads = []
    # create threads
    for _ in range(roop.globals.gpu_threads):
        thread = threading.Thread(target=process_frames, args=(source_path, temp_frame_paths, progress))
        threads.append(thread)
        thread.start()
    # join threads
    for thread in threads:
        thread.join()


def process_image(source_path: str, target_path: str, output_path: str) -> None:
    source_face = get_one_face(cv2.imread(source_path))
    target_frame = cv2.imread(target_path)
    result = process_faces(source_face, target_frame)
    cv2.imwrite(output_path, result)


def process_video(source_path: str, temp_frame_paths: List[str], mode: str) -> None:
    global FRAME_COUNTER
    FRAME_COUNTER = 0
    progress_bar_format = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
    total = len(temp_frame_paths)
    with tqdm(total=total, desc='Processing', unit='frame', dynamic_ncols=True, bar_format=progress_bar_format) as progress:
        if mode == 'cpu':
            progress.set_postfix({'mode': mode, 'cores': roop.globals.cpu_cores, 'memory': roop.globals.max_memory})
            process_frames(source_path, temp_frame_paths, progress)
        elif mode == 'gpu':
            progress.set_postfix({'mode': mode, 'threads': roop.globals.gpu_threads, 'memory': roop.globals.max_memory})
            multi_process_frame(source_path, temp_frame_paths, progress)
