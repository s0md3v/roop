import os
import shutil

sep = "/"
if os.name == "nt":
    sep = "\\"

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
    os.system(f'ffmpeg -framerate {fps} -pattern_type glob -i "{output_dir}{sep}*.png" -c:v libx264 -pix_fmt yuv420p -y "{output_dir}{sep}output.mp4"')


def extract_frames(input_path, output_dir):
    os.system(f'ffmpeg -i "{input_path}" "{output_dir}{sep}%04d.png"')


def add_audio(output_dir, target_path, keep_frames, output_file):
    video = target_path.split(sep)[-1]
    video_name = video.split(".")[0]
    save_to = output_file if output_file else output_dir + "{sep}swapped-" + video_name + ".mp4"
    os.system(f'ffmpeg -i "{output_dir}{sep}output.mp4" -i "{output_dir}{sep}{video}" -c:v copy -map 0:v:0 -map 1:a:0 -y "{save_to}"')
    if not os.path.isfile(save_to):
        shutil.move(output_dir + "{sep}output.mp4", save_to)
    if not keep_frames:
        shutil.rmtree(output_dir)


def is_img(path):
    return path.lower().endswith(("png", "jpg", "jpeg", "bmp"))

def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)
