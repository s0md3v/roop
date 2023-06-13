#!/usr/bin/env python3

import os
import sys


# single thread doubles cuda performance - needs to be set before torch import
if any(arg.startswith('--execution-provider') for arg in sys.argv):
    os.environ['OMP_NUM_THREADS'] = '1'
# reduce tensorflow log level
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import warnings
from typing import List
import platform
import signal
import shutil
import argparse
import psutil
import torch
import onnxruntime
import tensorflow
import multiprocessing
from opennsfw2 import predict_video_frames, predict_image
import cv2

import roop.globals
import roop.ui as ui
from roop.processors.frame.core import get_frame_processors_modules
from roop.utilities import has_image_extension, is_image, is_video, detect_fps, create_video, extract_frames, get_temp_frame_paths, restore_audio, create_temp, move_temp, clean_temp
from roop.face_analyser import get_one_face

if 'ROCMExecutionProvider' in roop.globals.execution_providers:
    del torch

warnings.simplefilter(action='ignore', category=FutureWarning)


def parse_args() -> None:
    signal.signal(signal.SIGINT, lambda signal_number, frame: destroy())
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--face', help='use a face image', dest='source_path')
    parser.add_argument('-t', '--target', help='replace image or video with face', dest='target_path')
    parser.add_argument('-o', '--output', help='save output to this file', dest='output_path')
    parser.add_argument('--frame-processor', help='list of frame processors to run', dest='frame_processor', default=['face_swapper'], choices=['face_swapper', 'face_enhancer'], nargs='+')
    parser.add_argument('--keep-fps', help='maintain original fps', dest='keep_fps', action='store_true', default=False)
    parser.add_argument('--keep-audio', help='maintain original audio', dest='keep_audio', action='store_true', default=True)
    parser.add_argument('--keep-frames', help='keep frames directory', dest='keep_frames', action='store_true', default=False)
    parser.add_argument('--many-faces', help='swap every face in the frame', dest='many_faces', action='store_true', default=False)
    parser.add_argument('--video-encoder', help='adjust output video encoder', dest='video_encoder', default='libx264', choices=['libx264', 'libx265', 'libvpx-vp9'])
    parser.add_argument('--video-quality', help='adjust output video quality', dest='video_quality', type=int, default=18)
    parser.add_argument('--max-memory', help='maximum amount of RAM in GB to be used', dest='max_memory', type=int, default=suggest_max_memory())
    parser.add_argument('--cpu-cores', help='number of CPU cores to use', dest='cpu_cores', type=int, default=suggest_cpu_cores())
    parser.add_argument('--execution-provider', help='execution provider', dest='execution_provider', default=['cpu'], choices=suggest_execution_providers(), nargs='+')
    parser.add_argument('--execution-threads', help='number of threads to be use for the GPU', dest='execution_threads', type=int, default=suggest_execution_threads())

    args = parser.parse_known_args()[0]

    roop.globals.source_path = args.source_path
    roop.globals.target_path = args.target_path
    roop.globals.output_path = args.output_path
    roop.globals.frame_processors = args.frame_processor
    roop.globals.headless = args.source_path or args.target_path or args.output_path
    roop.globals.keep_fps = args.keep_fps
    roop.globals.keep_audio = args.keep_audio
    roop.globals.keep_frames = args.keep_frames
    roop.globals.many_faces = args.many_faces
    roop.globals.video_encoder = args.video_encoder
    roop.globals.video_quality = args.video_quality
    roop.globals.max_memory = args.max_memory
    roop.globals.cpu_cores = args.cpu_cores
    roop.globals.execution_providers = decode_execution_providers(args.execution_provider)
    roop.globals.execution_threads = args.execution_threads

    # limit face enhancer to cuda
    if 'CUDAExecutionProvider' not in roop.globals.execution_providers and 'face_enhancer' in roop.globals.frame_processors:
        roop.globals.frame_processors.remove('face_enhancer')


def encode_execution_providers(execution_providers: List[str]) -> List[str]:
    return [execution_provider.replace('ExecutionProvider', '').lower() for execution_provider in execution_providers]


def decode_execution_providers(execution_providers: List[str]) -> List[str]:
    return [provider for provider, encoded_execution_provider in zip(onnxruntime.get_available_providers(), encode_execution_providers(onnxruntime.get_available_providers()))
            if any(execution_provider in encoded_execution_provider for execution_provider in execution_providers)]


def suggest_max_memory() -> int:
    if platform.system().lower() == 'darwin':
        return 4
    return 16


def suggest_cpu_cores() -> int:
    if platform.system().lower() == 'darwin':
        return 2
    return int(max(psutil.cpu_count() / 2, 1))


def suggest_execution_providers() -> List[str]:
    return encode_execution_providers(onnxruntime.get_available_providers())


def suggest_execution_threads() -> int:
    if 'DmlExecutionProvider' in roop.globals.execution_providers:
        return 1
    if 'ROCMExecutionProvider' in roop.globals.execution_providers:
        return 2
    return 8


def limit_resources() -> None:
    # prevent tensorflow memory leak
    gpus = tensorflow.config.experimental.list_physical_devices('GPU')
    for gpu in gpus:
        tensorflow.config.experimental.set_memory_growth(gpu, True)
    if roop.globals.max_memory:
        memory = roop.globals.max_memory * 1024 ** 3
        if platform.system().lower() == 'darwin':
            memory = roop.globals.max_memory * 1024 ** 6
        if platform.system().lower() == 'windows':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetProcessWorkingSetSize(-1, ctypes.c_size_t(memory), ctypes.c_size_t(memory))
        else:
            import resource
            resource.setrlimit(resource.RLIMIT_DATA, (memory, memory))


def release_resources() -> None:
    if 'CUDAExecutionProvider' in roop.globals.execution_providers:
        torch.cuda.empty_cache()


def pre_check() -> None:
    if sys.version_info < (3, 9):
        quit('Python version is not supported - please upgrade to 3.9 or higher.')
    if not shutil.which('ffmpeg'):
        quit('ffmpeg is not installed.')


def conditional_process_video(source_path: str, temp_frame_paths: List[str], process_video) -> None:
    pool_amount = len(temp_frame_paths) // roop.globals.cpu_cores
    if pool_amount > 2 and roop.globals.cpu_cores > 1 and roop.globals.execution_providers == ['CPUExecutionProvider']:
        POOL = multiprocessing.Pool(roop.globals.cpu_cores, maxtasksperchild=1)
        pools = []
        for i in range(0, len(temp_frame_paths), pool_amount):
            pool = POOL.apply_async(process_video, args=(source_path, temp_frame_paths[i:i + pool_amount], 'multi-processing'))
            pools.append(pool)
        for pool in pools:
            pool.get()
        POOL.close()
        POOL.join()
    else:
         process_video(roop.globals.source_path, temp_frame_paths, 'multi-threading')


def update_status(message: str) -> None:
    value = 'Status: ' + message
    print(value)
    if not roop.globals.headless:
        ui.update_status(value)


def start() -> None:
    if not roop.globals.source_path or not os.path.isfile(roop.globals.source_path):
        update_status('Select an image that contains a face.')
        return
    elif not roop.globals.target_path or not os.path.isfile(roop.globals.target_path):
        update_status('Select an image or video target!')
        return
    test_face = get_one_face(cv2.imread(roop.globals.source_path))
    if not test_face:
        update_status('No face detected in source image. Please try with another one!')
        return
    # process image to image
    if has_image_extension(roop.globals.target_path):
        if predict_image(roop.globals.target_path) > 0.85:
            destroy()
        for frame_processor in get_frame_processors_modules(roop.globals.frame_processors):
            update_status(f'{frame_processor} in progress...')
            frame_processor.process_image(roop.globals.source_path, roop.globals.target_path, roop.globals.output_path)
            release_resources()
        if is_image(roop.globals.target_path):
            update_status('Processing to image succeed!')
        else:
            update_status('Processing to image failed!')
        return
    # process image to videos
    seconds, probabilities = predict_video_frames(video_path=roop.globals.target_path, frame_interval=100)
    if any(probability > 0.85 for probability in probabilities):
        destroy()
    update_status('Creating temp resources...')
    create_temp(roop.globals.target_path)
    update_status('Extracting frames...')
    extract_frames(roop.globals.target_path)
    temp_frame_paths = get_temp_frame_paths(roop.globals.target_path)
    for frame_processor in get_frame_processors_modules(roop.globals.frame_processors):
        update_status(f'{frame_processor} in progress...')
        conditional_process_video(roop.globals.source_path, temp_frame_paths, frame_processor.process_video)
        release_resources()
    if roop.globals.keep_fps:
        update_status('Detecting fps...')
        fps = detect_fps(roop.globals.target_path)
        update_status(f'Creating video with {fps} fps...')
        create_video(roop.globals.target_path, fps)
    else:
        update_status('Creating video with 30.0 fps...')
        create_video(roop.globals.target_path)
    if roop.globals.keep_audio:
        if roop.globals.keep_fps:
            update_status('Restoring audio...')
        else:
            update_status('Restoring audio might cause issues as fps are not kept...')
        restore_audio(roop.globals.target_path, roop.globals.output_path)
    else:
        move_temp(roop.globals.target_path, roop.globals.output_path)
    clean_temp(roop.globals.target_path)
    if is_video(roop.globals.target_path):
        update_status('Processing to video succeed!')
    else:
        update_status('Processing to video failed!')


def destroy() -> None:
    if roop.globals.target_path:
        clean_temp(roop.globals.target_path)
    quit()


def run() -> None:
    parse_args()
    pre_check()
    for frame_processor in get_frame_processors_modules(roop.globals.frame_processors):
        frame_processor.pre_check()
    limit_resources()
    if roop.globals.headless:
        start()
    else:
        window = ui.init(start, destroy)
        window.mainloop()
