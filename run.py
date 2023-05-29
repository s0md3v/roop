import sys
import shutil
import core.globals

if not shutil.which('ffmpeg'):
    print('ffmpeg is not installed. Read the docs: https://github.com/s0md3v/roop#installation.\n' * 10)
    quit()
if '--gpu' not in sys.argv:
    core.globals.providers = ['CPUExecutionProvider']

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

for name, value in vars(parser.parse_args()).items():
    args[name] = value


sep = "/"
if os.name == "nt":
    sep = "\\"


def start_processing():
    if args['gpu']:
        process_video(args['source_img'], args["frame_paths"])
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


def preview_image(image_path):
    img = Image.open(image_path)
    img = img.resize((150, 150), Image.ANTIALIAS)
    photo_img = ImageTk.PhotoImage(img)
    left_frame = tk.Frame(window)
    left_frame.pack(side=tk.LEFT, padx=10, pady=10)
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
        img = img.resize((150, 150), Image.ANTIALIAS)
        photo_img = ImageTk.PhotoImage(img)
        right_frame = tk.Frame(window)
        right_frame.pack(side=tk.RIGHT, padx=10, pady=10)
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


def save_file():
   args['output_file'] = asksaveasfilename(initialfile='output.mp4', defaultextension=".mp4", filetypes=[("All Files","*.*"),("Videos","*.mp4")])


def status(string):
    status_label["text"] = string
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
        status("Swap successful!")
        return
    video_name = target_path.split("/")[-1].split(".")[0]
    output_dir = target_path.replace(target_path.split("/")[-1], "").rstrip("/") + "/" + video_name
    Path(output_dir).mkdir(exist_ok=True)
    status("Detecting video's FPS...")
    fps = detect_fps(target_path)
    if not args['keep_fps'] and fps > 30:
        this_path = output_dir + "/" + video_name + ".mp4"
        set_fps(target_path, this_path, 30)
        target_path, fps = this_path, 30
    else:
        shutil.copy(target_path, output_dir)
    status("Extracting frames...")
    extract_frames(target_path, output_dir)
    args['frame_paths'] = tuple(sorted(
        glob.glob(output_dir + f"/*.png"),
        key=lambda x: int(x.split(sep)[-1].replace(".png", ""))
    ))
    status("Swapping in progress...")
    start_processing()
    status("Creating video...")
    create_video(video_name, fps, output_dir)
    status("Adding audio...")
    add_audio(output_dir, target_path, args['keep_frames'], args['output_file'])
    save_path = args['output_file'] if args['output_file'] else output_dir + "/" + video_name + ".mp4"
    print("\n\nVideo saved as:", save_path, "\n\n")
    status("Swap successful!")


if __name__ == "__main__":
    global status_label, window
    if args['source_img']:
        start()
        quit()
    window = tk.Tk()
    window.geometry("600x350")
    window.title("roop")

    # Contact information
    support_link = tk.Label(window, text="Support the project ^_^", fg="red", cursor="hand2")
    support_link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/sponsors/s0md3v"))
    support_link.pack()

    # Select a face button
    face_button = tk.Button(window, text="Select a face", command=select_face)
    face_button.pack(padx=10, pady=20)

    # Select a target button
    target_button = tk.Button(window, text="Select a target", command=select_target)
    target_button.pack(padx=10, pady=10)

    # FPS limit checkbox
    limit_fps = tk.IntVar()
    fps_checkbox = tk.Checkbutton(window, text="Limit FPS to 30", variable=limit_fps, command=toggle_fps_limit, font=("Arial", 8))
    fps_checkbox.pack()
    fps_checkbox.select()

    # Start button
    start_button = tk.Button(window, text="Start", bg="#f1c40f", command=lambda: [save_file(), start()])
    start_button.pack(padx=10, pady=20)

    # Status label
    status_label = tk.Label(window, width=340, text="Waiting for input...", bg="black", fg="#2ecc71")
    status_label.pack()

    window.mainloop()
