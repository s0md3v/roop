#!/usr/bin/env python3

import platform
import signal
import sys
import shutil
import glob
import argparse
import os
import torch
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from opennsfw2 import predict_video_frames, predict_image
from tkinter.filedialog import asksaveasfilename
import webbrowser
import cv2
import threading
from PIL import Image, ImageTk

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
parser.add_argument('--gpu-vendor', help='choice your gpu vendor', dest='gpu_vendor', choices=['amd', 'intel', 'nvidia'])

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
        roop.globals.providers = ['CPUExecutionProvider']


def preview_image(image_path):
    img = Image.open(image_path)
    img = img.resize((180, 180), Image.ANTIALIAS)
    photo_img = ImageTk.PhotoImage(img)
    left_frame = tk.Frame(window)
    left_frame.place(x=60, y=100)
    img_label = tk.Label(left_frame, image=photo_img)
    img_label.image = photo_img
    img_label.pack()


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


def update_slider(video_path):
    return lambda frame_number: preview.update(get_video_frame(video_path, frame_number))


def process_test_preview(video_path):
    test_frame = process_faces(
        get_face_single(cv2.imread(args['source_img'])), 
        get_video_frame(video_path, preview.current_frame.get()),
        None
    )
    preview.update(test_frame)


def preview_handler(video_path):
    return lambda: preview_thread(process_test_preview(video_path))


def preview_video(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error opening video file")
        return
    ret, frame = cap.read()
    if ret:
        frame = get_video_frame(video_path)
        img = Image.fromarray(frame)
        img = img.resize((180, 180), Image.ANTIALIAS)
        photo_img = ImageTk.PhotoImage(img)
        right_frame = tk.Frame(window)
        right_frame.place(x=360, y=100)
        img_label = tk.Label(right_frame, image=photo_img)
        img_label.image = photo_img
        img_label.pack()

        # Preview
        preview.update(frame)
        amount_of_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        preview.init_slider(amount_of_frames, update_slider(video_path))
        preview.set_preview_handler(preview_handler(video_path))

    cap.release()


def select_face():
    args['source_img'] = filedialog.askopenfilename(title="Select a face")
    preview_image(args['source_img'])


def select_target():
    args['target_path'] = filedialog.askopenfilename(title="Select a target")
    threading.Thread(target=preview_video, args=(args['target_path'],)).start()


def toggle_fps_limit():
    args['keep_fps'] = int(limit_fps.get() != True)


def toggle_all_faces():
    roop.globals.all_faces = True if all_faces.get() == 1 else False


def toggle_keep_frames():
    args['keep_frames'] = int(keep_frames.get())


def save_file():
    filename, ext = 'output.mp4', '.mp4'
    if is_img(args['target_path']):
        filename, ext = 'output.png', '.png'
    args['output_file'] = asksaveasfilename(initialfile=filename, defaultextension=ext, filetypes=[("All Files","*.*"),("Videos","*.mp4")])


def status(string):
    if 'cli_mode' in args:
        print("Status: " + string)
    else:
        status_label["text"] = "Status: " + string
        window.update()


def start():
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
    process_video(args['source_img'], args["frame_paths"], preview.update)
    status("creating video...")
    create_video(video_name, exact_fps, output_dir)
    status("adding audio...")
    add_audio(output_dir, target_path, video_name_full, args['keep_frames'], args['output_file'])
    save_path = args['output_file'] if args['output_file'] else output_dir + "/" + video_name + ".mp4"
    print("\n\nVideo saved as:", save_path, "\n\n")
    status("swap successful!")


def preview_thread(thread_function):
    threading.Thread(target=thread_function).start()


def open_preview():
    if (preview.visible):
        preview.hide()
    else:
        preview.show()
        if args['target_path']:
            frame = get_video_frame(args['target_path'])
            preview.update(frame)


def run():
    global all_faces, keep_frames, limit_fps, status_label, window, preview

    pre_check()
    limit_resources()
    if args['source_img']:
        args['cli_mode'] = True
        start()
        quit()
    window = tk.Tk()
    window.geometry("600x700")
    window.title("roop")
    window.configure(bg="#2d3436")
    window.resizable(width=False, height=False)

    # Preview window
    preview = ui.PreviewWindow(window)

    # Contact information
    support_link = tk.Label(window, text="Donate to project <3", fg="#fd79a8", bg="#2d3436", cursor="hand2", font=("Arial", 8))
    support_link.place(x=180,y=20,width=250,height=30)
    support_link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/sponsors/s0md3v"))

    # Select a face button
    face_button = tk.Button(window, text="Select a face", command=select_face, bg="#2d3436", fg="#74b9ff", highlightthickness=4, relief="flat", highlightbackground="#74b9ff", activebackground="#74b9ff", borderwidth=4)
    face_button.place(x=60,y=320,width=180,height=80)

    # Select a target button
    target_button = tk.Button(window, text="Select a target", command=select_target, bg="#2d3436", fg="#74b9ff", highlightthickness=4, relief="flat", highlightbackground="#74b9ff", activebackground="#74b9ff", borderwidth=4)
    target_button.place(x=360,y=320,width=180,height=80)

    # All faces checkbox
    all_faces = tk.IntVar()
    all_faces_checkbox = tk.Checkbutton(window, anchor="w", relief="groove", activebackground="#2d3436", activeforeground="#74b9ff", selectcolor="black", text="Process all faces in frame", fg="#dfe6e9", borderwidth=0, highlightthickness=0, bg="#2d3436", variable=all_faces, command=toggle_all_faces)
    all_faces_checkbox.place(x=60,y=500,width=240,height=31)

    # FPS limit checkbox
    limit_fps = tk.IntVar(None, not args['keep_fps'])
    fps_checkbox = tk.Checkbutton(window, anchor="w", relief="groove", activebackground="#2d3436", activeforeground="#74b9ff", selectcolor="black", text="Limit FPS to 30", fg="#dfe6e9", borderwidth=0, highlightthickness=0, bg="#2d3436", variable=limit_fps, command=toggle_fps_limit)
    fps_checkbox.place(x=60,y=475,width=240,height=31)

    # Keep frames checkbox
    keep_frames = tk.IntVar(None, args['keep_frames'])
    frames_checkbox = tk.Checkbutton(window, anchor="w", relief="groove", activebackground="#2d3436", activeforeground="#74b9ff", selectcolor="black", text="Keep frames dir", fg="#dfe6e9", borderwidth=0, highlightthickness=0, bg="#2d3436", variable=keep_frames, command=toggle_keep_frames)
    frames_checkbox.place(x=60,y=450,width=240,height=31)

    # Start button
    start_button = tk.Button(window, text="Start", bg="#f1c40f", relief="flat", borderwidth=0, highlightthickness=0, command=lambda: [save_file(), preview_thread(start)])
    start_button.place(x=170,y=560,width=120,height=49)

    # Preview button
    preview_button = tk.Button(window, text="Preview", bg="#f1c40f", relief="flat", borderwidth=0, highlightthickness=0, command=lambda: [open_preview()])
    preview_button.place(x=310,y=560,width=120,height=49)

    # Status label
    status_label = tk.Label(window, width=580, justify="center", text="Status: waiting for input...", fg="#2ecc71", bg="#2d3436")
    status_label.place(x=10,y=640,width=580,height=30)

    window.mainloop()
