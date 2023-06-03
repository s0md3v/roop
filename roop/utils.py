import os
import shutil
import roop.globals

sep = "/"
if os.name == "nt":
    sep = "\\"


def path(string):
    if sep == "\\":
        return string.replace("/", "\\")
    return string


def run_command(command, mode="silent"):
    if mode == "debug":
        return os.system(command)
    return os.popen(command).read()


def detect_fps(input_path):
    input_path = path(input_path)
    output = os.popen(f'ffprobe -v error -select_streams v -of default=noprint_wrappers=1:nokey=1 -show_entries stream=r_frame_rate "{input_path}"').read()
    if "/" in output:
        try:
            return int(output.split("/")[0]) // int(output.split("/")[1].strip()), output.strip()
        except:
            pass
    return 30, 30


def run_ffmpeg(args):
    log_level = f'-loglevel {roop.globals.log_level}'
    run_command(f'ffmpeg {log_level} {args}')


def set_fps(input_path, output_path, fps):
    input_path, output_path = path(input_path), path(output_path)
    run_ffmpeg(f'-i "{input_path}" -filter:v fps=fps={fps} "{output_path}"')


def create_video(video_name, fps, output_dir):
    hwaccel_option = '-hwaccel cuda' if roop.globals.gpu_vendor == 'nvidia' else ''
    output_dir = path(output_dir)
    run_ffmpeg(f'{hwaccel_option} -framerate "{fps}" -i "{output_dir}{sep}%04d.png" -c:v libx264 -crf 7 -pix_fmt yuv420p -y "{output_dir}{sep}output.mp4"')


def extract_frames(input_path, output_dir):
    hwaccel_option = '-hwaccel cuda' if roop.globals.gpu_vendor == 'nvidia' else ''
    input_path, output_dir = path(input_path), path(output_dir)
    run_ffmpeg(f' {hwaccel_option} -i "{input_path}" "{output_dir}{sep}%04d.png"')


def add_audio(output_dir, target_path, video, keep_frames, output_file):
    video_name = os.path.splitext(video)[0]
    save_to = output_file if output_file else output_dir + "/swapped-" + video_name + ".mp4"
    save_to_ff, output_dir_ff = path(save_to), path(output_dir)
    run_ffmpeg(f'-i "{output_dir_ff}{sep}output.mp4" -i "{output_dir_ff}{sep}{video}" -c:v copy -map 0:v:0 -map 1:a:0 -y "{save_to_ff}"')
    if not os.path.isfile(save_to):
        shutil.move(output_dir + "/output.mp4", save_to)
    if not keep_frames:
        shutil.rmtree(output_dir)


def is_img(path):
    return path.lower().endswith(("png", "jpg", "jpeg", "bmp"))


def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)
