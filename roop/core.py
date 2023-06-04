#!/usr/bin/env python3

import os
import sys
# single thread doubles performance of gpu-mode - needs to be set before torch import
if any(arg.startswith('--gpu-vendor=') for arg in sys.argv):
    os.environ['OMP_NUM_THREADS'] = '1'
import platform
import signal
import shutil
import glob
import argparse
import torch
from pathlib import Path
from opennsfw2 import predict_video_frames, predict_image
import cv2

import roop.globals
from roop.swapper import process_video, process_img, process_faces
from roop.utils import is_img, detect_fps, set_fps, create_video, add_audio, extract_frames, rreplace
from roop.analyser import get_face_single
import roop.ui as ui

if 'ROCMExecutionProvider' in roop.globals.providers:
    del torch

signal.signal(signal.SIGINT, lambda signal_number, frame: quit())
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--face', help='use this face', dest='source_img')
parser.add_argument('-t', '--target', help='replace this face', dest='target_path')
parser.add_argument('-o', '--output', help='save output to this file', dest='output_file')
parser.add_argument('--keep-fps', help='maintain original fps', dest='keep_fps', action='store_true', default=False)
parser.add_argument('--keep-frames', help='keep frames directory', dest='keep_frames', action='store_true', default=False)
parser.add_argument('--all-faces', help='swap all faces in frame', dest='all_faces', action='store_true', default=False)
parser.add_argument('--max-memory', help='maximum amount of RAM in GB to be used', dest='max_memory', type=int)
parser.add_argument('--cpu-threads', help='number of threads to be use for CPU mode', dest='cpu_threads', type=int)
parser.add_argument('--gpu-threads', help='number of threads to be use for GPU mode', dest='gpu_threads', type=int)
parser.add_argument('--gpu-vendor', help='choice your gpu vendor', dest='gpu_vendor', choices=['apple', 'amd', 'intel', 'nvidia'])

args = {}
for name, value in vars(parser.parse_args()).items():
    args[name] = value

if 'all_faces' in args:
    roop.globals.all_faces = True

if 'cpu_threads' in args and args['cpu_threads']:
    roop.globals.cpu_threads = args['cpu_threads']

if 'gpu_threads' in args and args['gpu_threads']:
    roop.globals.gpu_threads = args['gpu_threads']

if 'gpu_vendor' in args and args['gpu_vendor']:
    roop.globals.gpu_vendor = args['gpu_vendor']

sep = "/"
if os.name == "nt":
    sep = "\\"


def limit_resources():
    if args['max_memory']:
        memory = args['max_memory'] * 1024 * 1024 * 1024
        if str(platform.system()).lower() == 'windows':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetProcessWorkingSetSize(-1, ctypes.c_size_t(memory), ctypes.c_size_t(memory))
        else:
            import resource
            resource.setrlimit(resource.RLIMIT_DATA, (memory, memory))


def pre_check():
    if sys.version_info < (3, 9):
        quit('Python version is not supported - please upgrade to 3.9 or higher')
    if not shutil.which('ffmpeg'):
        quit('ffmpeg is not installed!')
    model_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../inswapper_128.onnx')
    if not os.path.isfile(model_path):
        quit('File "inswapper_128.onnx" does not exist!')
    if roop.globals.gpu_vendor == 'apple':
        if 'CoreMLExecutionProvider' not in roop.globals.providers:
            quit("You are using --gpu=apple flag but CoreML isn't available or properly installed on your system.")
    if roop.globals.gpu_vendor == 'amd':
        if 'ROCMExecutionProvider' not in roop.globals.providers:
            quit("You are using --gpu=amd flag but ROCM isn't available or properly installed on your system.")
    if roop.globals.gpu_vendor == 'nvidia':
        CUDA_VERSION = torch.version.cuda
        CUDNN_VERSION = torch.backends.cudnn.version()
        if not torch.cuda.is_available() or not CUDA_VERSION:
            quit("You are using --gpu=nvidia flag but CUDA isn't available or properly installed on your system.")
        if CUDA_VERSION > '11.8':
            quit(f"CUDA version {CUDA_VERSION} is not supported - please downgrade to 11.8")
        if CUDA_VERSION < '11.4':
            quit(f"CUDA version {CUDA_VERSION} is not supported - please upgrade to 11.8")
        if CUDNN_VERSION < 8220:
            quit(f"CUDNN version {CUDNN_VERSION} is not supported - please upgrade to 8.9.1")
        if CUDNN_VERSION > 8910:
            quit(f"CUDNN version {CUDNN_VERSION} is not supported - please downgrade to 8.9.1")
    else:
        for provider in ['CUDAExecutionProvider', 'TensorrtExecutionProvider']:
            if provider in roop.globals.providers:
                roop.globals.providers = roop.globals.providers.remove(provider)


def get_video_frame(video_path, frame_number = 1):
    cap = cv2.VideoCapture(video_path)
    amount_of_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.set(cv2.CAP_PROP_POS_FRAMES, min(amount_of_frames, frame_number-1))
    if not cap.isOpened():
        print("Error opening video file")
        return
    ret, frame = cap.read()
    if ret:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    cap.release()


def preview_video(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error opening video file")
        return 0
    amount_of_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    ret, frame = cap.read()
    if ret:
        frame = get_video_frame(video_path)

    cap.release()
    return (amount_of_frames, frame)


def status(string):
    value = "Status: " + string
    if 'cli_mode' in args:
        print(value)
    else:
        ui.update_status_label(value)


def start(preview_callback = None):
    if not args['source_img'] or not os.path.isfile(args['source_img']):
        print("\n[WARNING] Please select an image containing a face.")
        return
    elif not args['target_path'] or not os.path.isfile(args['target_path']):
        print("\n[WARNING] Please select a video/image to swap face in.")
        return
    if not args['output_file']:
        target_path = args['target_path']
        args['output_file'] = rreplace(target_path, "/", "/swapped-", 1) if "/" in target_path else "swapped-" + target_path
    target_path = args['target_path']
    test_face = get_face_single(cv2.imread(args['source_img']))
    if not test_face:
        print("\n[WARNING] No face detected in source image. Please try with another one.\n")
        return
    if is_img(target_path):
        if predict_image(target_path) > 0.85:
            quit()
        process_img(args['source_img'], target_path, args['output_file'])
        status("swap successful!")
        return
    seconds, probabilities = predict_video_frames(video_path=args['target_path'], frame_interval=100)
    if any(probability > 0.85 for probability in probabilities):
        quit()
    video_name_full = target_path.split("/")[-1]
    video_name = os.path.splitext(video_name_full)[0]
    output_dir = os.path.dirname(target_path) + "/" + video_name
    Path(output_dir).mkdir(exist_ok=True)
    status("detecting video's FPS...")
    fps, exact_fps = detect_fps(target_path)
    if not args['keep_fps'] and fps > 30:
        this_path = output_dir + "/" + video_name + ".mp4"
        set_fps(target_path, this_path, 30)
        target_path, exact_fps = this_path, 30
    else:
        shutil.copy(target_path, output_dir)
    status("extracting frames...")
    extract_frames(target_path, output_dir)
    args['frame_paths'] = tuple(sorted(
        glob.glob(output_dir + "/*.png"),
        key=lambda x: int(x.split(sep)[-1].replace(".png", ""))
    ))
    status("swapping in progress...")
    process_video(args['source_img'], args["frame_paths"], preview_callback)
    status("creating video...")
    create_video(video_name, exact_fps, output_dir)
    status("adding audio...")
    add_audio(output_dir, target_path, video_name_full, args['keep_frames'], args['output_file'])
    save_path = args['output_file'] if args['output_file'] else output_dir + "/" + video_name + ".mp4"
    print("\n\nVideo saved as:", save_path, "\n\n")
    status("swap successful!")


def select_face_handler(path: str):
    args['source_img'] = path


def select_target_handler(path: str):
    args['target_path'] = path
    return preview_video(args['target_path'])


def toggle_all_faces_handler(value: int):
    roop.globals.all_faces = True if value == 1 else False


def toggle_fps_limit_handler(value: int):
    args['keep_fps'] = int(value != 1)


def toggle_keep_frames_handler(value: int):
    args['keep_frames'] = value


def save_file_handler(path: str):
    args['output_file'] = path


def create_test_preview(frame_number):
    return process_faces(
        get_face_single(cv2.imread(args['source_img'])), 
        get_video_frame(args['target_path'], frame_number),
        None
    )


def run():
    global all_faces, keep_frames, limit_fps

    pre_check()
    limit_resources()
    if args['source_img']:
        args['cli_mode'] = True
        start()
        quit()

    window = ui.init(
        {
            'all_faces': roop.globals.all_faces,
            'keep_fps': args['keep_fps'],
            'keep_frames': args['keep_frames']
        },
        select_face_handler,
        select_target_handler,
        toggle_all_faces_handler,
        toggle_fps_limit_handler,
        toggle_keep_frames_handler,
        save_file_handler,
        start,
        get_video_frame,
        create_test_preview
    )

    window.mainloop()
