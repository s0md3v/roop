#!/usr/bin/env python3

import platform
import sys
import time
import torch
import shutil
import core.globals
import glob
import argparse
import multiprocessing as mp
import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from tkinter.filedialog import asksaveasfilename
from core.processor import process_video, process_img
from core.utils import is_img, detect_fps, set_fps, create_video, add_audio, extract_frames
from core.config import get_face
import webbrowser
import psutil
import cv2
import threading
from PIL import Image, ImageTk

pool = None
args = {}

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--face', help='use this face', dest='source_img')
parser.add_argument('-t', '--target', help='replace this face', dest='target_path')
parser.add_argument('-o', '--output', help='save output to this file', dest='output_file')
parser.add_argument('--keep-fps', help='maintain original fps', dest='keep_fps', action='store_true', default=False)
parser.add_argument('--gpu', help='use gpu', dest='gpu', action='store_true', default=False)
parser.add_argument('--keep-frames', help='keep frames directory', dest='keep_frames', action='store_true', default=False)
parser.add_argument('--max-memory', help='set max memory', default=16, type=int)

for name, value in vars(parser.parse_args()).items():
    args[name] = value

sep = "/"
if os.name == "nt":
    sep = "\\"


def limit_resources():
    if args['max_memory'] >= 1:
        memory = args['max_memory'] * 1024 * 1024 * 1024
        if str(platform.system()).lower() == 'windows':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetProcessWorkingSetSize(-1, ctypes.c_size_t(memory), ctypes.c_size_t(memory))
        else:
            import resource
            resource.setrlimit(resource.RLIMIT_DATA, (memory, memory))


def pre_check():
    if sys.version_info < (3, 8):
        quit(f'Python version is not supported - please upgrade to 3.8 or higher')
    if not shutil.which('ffmpeg'):
        quit('ffmpeg is not installed!')
    if os.path.isfile('../inswapper_128.onnx'):
        quit('File "inswapper_128.onnx" does not exist!')
    if '--gpu' in sys.argv:
        CUDA_VERSION = torch.version.cuda
        CUDNN_VERSION = torch.backends.cudnn.version()

        if 'ROCMExecutionProvider' not in core.globals.providers:
            if CUDA_VERSION > '11.8':
                quit(f"CUDA version {CUDA_VERSION} is not supported - please downgrade to 11.8.")
            if CUDA_VERSION < '11.4':
                quit(f"CUDA version {CUDA_VERSION} is not supported - please upgrade to 11.8")
            if CUDNN_VERSION < 8220:
                quit(f"CUDNN version {CUDNN_VERSION} is not supported - please upgrade to 8.9.1")
            if CUDNN_VERSION > 8910:
                quit(f"CUDNN version {CUDNN_VERSION} is not supported - please downgrade to 8.9.1")
            if not torch.cuda.is_available():
                quit("You are using --gpu flag but CUDA isn't available or properly installed on your system.")
    else:
        core.globals.providers = ['CPUExecutionProvider']


def start_processing():
    start_time = time.time()
    if args['gpu']:
        process_video(args['source_img'], args["frame_paths"])
        end_time = time.time()
        print(flush=True)
        print(f"Processing time: {end_time - start_time:.2f} seconds", flush=True)
        return
    frame_paths = args["frame_paths"]
    n = len(frame_paths)//(psutil.cpu_count()-1)
    processes = []
    for i in range(0, len(frame_paths), n):
        p = pool.apply_async(process_video, args=(args['source_img'], frame_paths[i:i+n],))
        processes.append(p)
    for p in processes:
        p.get()
    pool.close()
    pool.join()
    end_time = time.time()
    print(flush=True)
    print(f"Processing time: {end_time - start_time:.2f} seconds", flush=True)


def preview_image(image_path):
    img = Image.open(image_path)
    img = img.resize((180, 180), Image.ANTIALIAS)
    photo_img = ImageTk.PhotoImage(img)
    left_frame = tk.Frame(window)
    left_frame.place(x=60, y=100)
    img_label = tk.Label(left_frame, image=photo_img)
    img_label.image = photo_img
    img_label.pack()


def preview_video(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error opening video file")
        return
    ret, frame = cap.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        img = img.resize((180, 180), Image.ANTIALIAS)
        photo_img = ImageTk.PhotoImage(img)
        right_frame = tk.Frame(window)
        right_frame.place(x=360, y=100)
        img_label = tk.Label(right_frame, image=photo_img)
        img_label.image = photo_img
        img_label.pack()

    cap.release()


def select_face():
    args['source_img'] = filedialog.askopenfilename(title="Select a face")
    preview_image(args['source_img'])


def select_target():
    args['target_path'] = filedialog.askopenfilename(title="Select a target")
    threading.Thread(target=preview_video, args=(args['target_path'],)).start()


def toggle_fps_limit():
    args['keep_fps'] = limit_fps.get() != True


def toggle_keep_frames():
    args['keep_frames'] = keep_frames.get() != True


def save_file():
    args['output_file'] = asksaveasfilename(initialfile='output.mp4', defaultextension=".mp4", filetypes=[("All Files","*.*"),("Videos","*.mp4")])


def status(string):
    if 'cli_mode' in args:
        print("Status: " + string)
    else:
        status_label["text"] = "Status: " + string
        window.update()


def start():
    print("DON'T WORRY. IT'S NOT STUCK/CRASHED.\n" * 5)
    if not args['source_img'] or not os.path.isfile(args['source_img']):
        print("\n[WARNING] Please select an image containing a face.")
        return
    elif not args['target_path'] or not os.path.isfile(args['target_path']):
        print("\n[WARNING] Please select a video/image to swap face in.")
        return
    global pool
    pool = mp.Pool(psutil.cpu_count()-1)
    target_path = args['target_path']
    test_face = get_face(cv2.imread(args['source_img']))
    if not test_face:
        print("\n[WARNING] No face detected in source image. Please try with another one.\n")
        return
    if is_img(target_path):
        process_img(args['source_img'], target_path)
        status("swap successful!")
        return
    video_name = target_path.split("/")[-1].split(".")[0]
    output_dir = target_path.replace(target_path.split("/")[-1], "").rstrip("/") + "/" + video_name
    Path(output_dir).mkdir(exist_ok=True)
    status("detecting video's FPS...")
    fps = detect_fps(target_path)
    if not args['keep_fps'] and fps > 30:
        this_path = output_dir + "/" + video_name + ".mp4"
        set_fps(target_path, this_path, 30)
        target_path, fps = this_path, 30
    else:
        shutil.copy(target_path, output_dir)
    status("extracting frames...")
    extract_frames(target_path, output_dir)
    args['frame_paths'] = tuple(sorted(
        glob.glob(output_dir + f"/*.png"),
        key=lambda x: int(x.split(sep)[-1].replace(".png", ""))
    ))
    status("swapping in progress...")
    start_processing()
    status("creating video...")
    create_video(video_name, fps, output_dir)
    status("adding audio...")
    add_audio(output_dir, target_path, args['keep_frames'], args['output_file'])
    save_path = args['output_file'] if args['output_file'] else output_dir + "/" + video_name + ".mp4"
    print("\n\nVideo saved as:", save_path, "\n\n")
    status("swap successful!")


if __name__ == "__main__":
    global status_label, window

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

    # FPS limit checkbox
    limit_fps = tk.IntVar()
    fps_checkbox = tk.Checkbutton(window, relief="groove", activebackground="#2d3436", activeforeground="#74b9ff", selectcolor="black", text="Limit FPS to 30", fg="#dfe6e9", borderwidth=0, highlightthickness=0, bg="#2d3436", variable=limit_fps, command=toggle_fps_limit)
    fps_checkbox.place(x=30,y=500,width=240,height=31)
    fps_checkbox.select()

    # Keep frames checkbox
    keep_frames = tk.IntVar()
    frames_checkbox = tk.Checkbutton(window, relief="groove", activebackground="#2d3436", activeforeground="#74b9ff", selectcolor="black", text="Keep frames dir", fg="#dfe6e9", borderwidth=0, highlightthickness=0, bg="#2d3436", variable=keep_frames, command=toggle_keep_frames)
    frames_checkbox.place(x=37,y=450,width=240,height=31)

    # Start button
    start_button = tk.Button(window, text="Start", bg="#f1c40f", relief="flat", borderwidth=0, highlightthickness=0, command=lambda: [save_file(), start()])
    start_button.place(x=240,y=560,width=120,height=49)

    # Status label
    status_label = tk.Label(window, width=580, justify="center", text="Status: waiting for input...", fg="#2ecc71", bg="#2d3436")
    status_label.place(x=10,y=640,width=580,height=30)
    
    window.mainloop()
