import os
import shutil
from pathlib import Path

def run_command(command, mode="silent"):
    if mode == "debug":
        return os.system(command)
    return os.popen(command).read()


def detect_fps(input_path):
    output = os.popen(f'ffprobe -v error -select_streams v -of default=noprint_wrappers=1:nokey=1 -show_entries stream=r_frame_rate "{input_path}"').read()
    if "/" in output:
        try:
            return int(output.split("/")[0]) // int(output.split("/")[1])
        except:
            pass
    return 60


def set_fps(input_path, output_path, fps):
    os.system(f'ffmpeg -i "{input_path}" -filter:v fps=fps={fps} "{output_path}"')


def create_video(video_name, fps, output_dir):
    os.system(f'ffmpeg -framerate {fps} -i "{output_dir}/%04d.png" -c:v libx264 -crf 7 -pix_fmt yuv420p -y "{output_dir}/output.mp4"')


def extract_frames(input_path, output_dir):
    os.system(f'ffmpeg -i "{input_path}" "{output_dir}/%04d.png"')


def add_audio(output_dir, target_path, keep_frames, output_file):
    rendered_video = output_dir / 'output.mp4'
    save_to = output_file if output_file else output_dir / f"swapped-{target_path.name}"
    os.system(f'ffmpeg -i "{rendered_video}" -i "{target_path}" -c:v copy -map 0:v:0 -map 1:a:0 -y "{save_to}"')
    if not os.path.isfile(save_to):
        shutil.move(output_dir + f"/output.mp4", save_to)
    if not keep_frames:
        shutil.rmtree(output_dir)


def is_img(path):
    return path.suffix.endswith(("png", "jpg", "jpeg", "bmp"))

def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)
