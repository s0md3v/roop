import sys
import onnxruntime
import core.globals

if '--gpu' in sys.argv:
    core.globals.providers = onnxruntime.get_available_providers()

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
import shutil
import cv2

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

sep = "/" # used for filepaths e.g. /root/path/output.mp4
if os.name == 'nt':
    sep = "\\" # for windows

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


def select_face():
    args['source_img'] = filedialog.askopenfilename(title="Select a face")


def select_target():
    args['target_path'] = filedialog.askopenfilename(title="Select a target")


def toggle_fps_limit():
    args['keep_fps'] = limit_fps.get() != True


def save_file():
   args['output_file'] = asksaveasfilename(initialfile='output.mp4', defaultextension=".mp4", filetypes=[("All Files","*.*"),("Videos","*.mp4")])


def start():
    print("DON'T WORRY. IT'S NOT STUCK.\n" * 5)
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
        return
    video_name = target_path.split(sep)[-1].split(".")[0]
    output_dir = target_path.replace(target_path.split(sep)[-1], "") + sep + video_name
    if sep == "\\":
        output_dir = output_dir.lstrip("\\")
    Path(output_dir).mkdir(exist_ok=True)
    fps = detect_fps(target_path)
    if not args['keep_fps'] and fps > 30:
        this_path = output_dir + sep + video_name + ".mp4"
        set_fps(target_path, this_path, 30)
        target_path, fps = this_path, 30
    else:
        shutil.copy(target_path, output_dir)
    extract_frames(target_path, output_dir)
    args['frame_paths'] = tuple(sorted(
        glob.glob(output_dir + "/*.png"),
        key=lambda x: int(x.split(sep)[-1].replace(".png", ""))
    ))
    start_processing()
    create_video(video_name, fps, output_dir)
    add_audio(output_dir, target_path, args['keep_frames'], args['output_file'])
    save_path = args['output_file'] if args['output_file'] else output_dir + sep + video_name + ".mp4"
    print("\n\nVideo saved as:", save_path, "\n\n")


if __name__ == "__main__":
    if args['source_img']:
        start()
        quit()
    window = tk.Tk()
    window.geometry("600x200")
    window.title("roop")

    # Contact information
    support_link = tk.Label(window, text="Support the project ^_^", fg="red", cursor="hand2")
    support_link.pack(padx=10, pady=10)
    support_link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/sponsors/s0md3v"))

    # Select a face button
    face_button = tk.Button(window, text="Select a face", command=select_face)
    face_button.pack(side=tk.LEFT, padx=10, pady=10)

    # Select a target button
    target_button = tk.Button(window, text="Select a target", command=select_target)
    target_button.pack(side=tk.RIGHT, padx=10, pady=10)

    # FPS limit checkbox
    limit_fps = tk.IntVar()
    fps_checkbox = tk.Checkbutton(window, text="Limit FPS to 30", variable=limit_fps, command=toggle_fps_limit, font=("Arial", 8))
    fps_checkbox.pack(side=tk.BOTTOM)
    fps_checkbox.select()

    # Start button
    start_button = tk.Button(window, text="Start", bg="green", command=lambda: [save_file(), start()])
    start_button.pack(side=tk.BOTTOM, padx=10, pady=10)
    window.mainloop()
