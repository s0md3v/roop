import glob
import os
import shutil
import subprocess
from pathlib import Path
from typing import List
import cv2
from PIL import Image

import roop.globals

TEMP_FILE = 'temp.mp4'
TEMP_DIRECTORY = 'temp'


def run_ffmpeg(args: List) -> None:
    commands = ['ffmpeg', '-hide_banner', '-hwaccel', 'auto', '-loglevel', roop.globals.log_level]
    commands.extend(args)
    try:
        subprocess.check_output(commands, stderr=subprocess.STDOUT)
    except Exception:
        pass


def detect_fps(target_path: str) -> int:
    command = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate', '-of', 'default=noprint_wrappers=1:nokey=1', target_path]
    output = subprocess.check_output(command).decode().strip()
    try:
        return int(eval(output))
    except Exception:
        pass
    return 30


def extract_frames(target_path: str) -> None:
    temp_directory_path = get_temp_directory_path(target_path)
    run_ffmpeg(['-i', target_path, os.path.join(temp_directory_path, '%04d.png')])


def create_video(target_path: str, fps: int) -> None:
    temp_directory_path = get_temp_directory_path(target_path)
    run_ffmpeg(['-i', os.path.join(temp_directory_path, '%04d.png'), '-framerate', str(fps), '-c:v', roop.globals.video_encoder, '-crf', str(roop.globals.video_quality), '-pix_fmt', 'yuv420p', '-y', get_temp_file_path(target_path)])


def restore_audio(target_path: str, output_path: str) -> None:
    temp_file_path = get_temp_file_path(target_path)
    run_ffmpeg(['-i', temp_file_path, '-i', target_path, '-c:v', 'copy', '-map', '0:v:0', '-map', '1:a:0', '-y', output_path])
    if not os.path.isfile(output_path):
        move_temp(target_path, output_path)


def get_temp_frames_paths(target_path: str) -> List:
    temp_directory_path = get_temp_directory_path(target_path)
    return glob.glob(os.path.join(temp_directory_path, '*.png'))


def get_temp_directory_path(target_path: str) -> str:
    target_name, _ = os.path.splitext(os.path.basename(target_path))
    target_directory_path = os.path.dirname(target_path)
    return os.path.join(target_directory_path, TEMP_DIRECTORY, target_name)


def get_temp_file_path(target_path: str) -> str:
    temp_directory_path = get_temp_directory_path(target_path)
    return os.path.join(temp_directory_path, TEMP_FILE)


def create_temp(target_path: str) -> None:
    temp_directory_path = get_temp_directory_path(target_path)
    Path(temp_directory_path).mkdir(parents=True, exist_ok=True)


def move_temp(target_path: str, output_path: str) -> None:
    temp_file_path = get_temp_file_path(target_path)
    if os.path.isfile(temp_file_path):
        shutil.move(temp_file_path, output_path)


def clean_temp(target_path: str) -> None:
    temp_directory_path = get_temp_directory_path(target_path)
    parent_directory_path = os.path.dirname(temp_directory_path)
    if not roop.globals.keep_frames and os.path.isdir(temp_directory_path):
        shutil.rmtree(temp_directory_path)
    if os.path.exists(parent_directory_path) and not os.listdir(parent_directory_path):
        os.rmdir(parent_directory_path)


def has_image_extention(image_path: str) -> bool:
    return image_path.lower().endswith(('png', 'jpg', 'jpeg'))


def is_image(image_path: str) -> bool:
    if image_path and os.path.isfile(image_path):
        try:
            image = Image.open(image_path)
            image.verify()
            return True
        except Exception:
            pass
    return False


def is_video(video_path: str) -> bool:
    if video_path and os.path.isfile(video_path):
        try:
            capture = cv2.VideoCapture(video_path)
            if capture.isOpened():
                is_video, _ = capture.read()
                capture.release()
                return is_video
        except Exception:
            pass
    return False
