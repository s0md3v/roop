import os
import time
from typing import Callable

import gradio as gr
from moviepy.editor import VideoFileClip

import roop.globals

OUTPUT_PATH = "output"
os.makedirs(OUTPUT_PATH, exist_ok=True)

start_func = None


def has_image_extension(image_path: str) -> bool:
    return image_path.lower().endswith(('png', 'jpg', 'jpeg', 'webp', 'gif'))


def has_video_extension(image_path: str) -> bool:
    return image_path.lower().endswith(('mp4'))


def mp42gif(video):
    gif = video[:-3] + 'gif'
    video = VideoFileClip(video)
    video.write_gif(gif)
    return gif


def gif2mp4(gif):
    video = gif[:-3] + 'mp4'
    gif = VideoFileClip(gif)
    gif.write_videofile(video, fps=gif.fps)
    return video


def submit_func(source, target, keep_fps, many_faces, keep_audio=False, keep_frames=False, video_quality=-1):
    if source is None:
        raise gr.Error("Please upload your source file!")
        return gr.update(), gr.update()

    if target is None:
        raise gr.Error("Please upload your target file!")
        return gr.update(), gr.update()

    source = source.name
    target = target.name

    gif_flag = False
    if target.endswith('.gif'):
        gif_flag = True
        target = gif2mp4(target)

    suffix = os.path.splitext(target)[-1]
    output_filepath = os.path.join(OUTPUT_PATH,
                                   'output-{timestamp}{suffix}'.format(suffix=suffix, timestamp=int(time.time())))

    roop.globals.source_path = source
    roop.globals.target_path = target
    roop.globals.output_path = output_filepath

    roop.globals.keep_fps = keep_fps
    roop.globals.many_faces = many_faces
    roop.globals.keep_audio = keep_audio
    roop.globals.keep_frames = keep_frames
    roop.globals.video_quality = video_quality

    global start_func
    start_func()

    if gif_flag:
        output_filepath = mp42gif(output_filepath)

    if has_image_extension(output_filepath):
        return gr.update(value=output_filepath, visible=True), gr.update(visible=False)

    if has_video_extension(output_filepath):
        return gr.update(visible=False), gr.update(value=output_filepath, visible=True)


def show_source_file(file):
    if file is None:
        return gr.update()

    return file.name


def show_target_file(file):
    if file is None:
        return gr.update(), gr.update()

    if has_image_extension(file.name):
        return gr.update(value=file.name, visible=True), gr.update(visible=False)

    if has_video_extension(file.name):
        return gr.update(visible=False), gr.update(value=file.name, visible=True)


def init(start: Callable[[], None], destroy: Callable[[], None]):
    global start_func
    start_func = start

    with gr.Blocks() as demo:
        gr.Markdown("# Welcome to use the Face Swapper !")

        with gr.Row():
            source_file = gr.File(file_count='single', file_types=['.png', '.jpg', '.jpeg', '.webp'],
                                  type='file', label='source')
            target_file = gr.File(file_count='single', file_types=['.png', '.jpg', '.jpeg', '.webp', '.gif', '.mp4'],
                                  type='file', label='target')

        with gr.Row():
            source_img = gr.Image(type='filepath', label="source", interactive=False, height=300)
            target_img = gr.Image(type='filepath', label="target image", interactive=False, height=300, visible=True)
            target_video = gr.Video(label="target video", interactive=False, visible=False)

        with gr.Row():
            keep_fps = gr.Checkbox(value=False, label="Keep fps")
            many_face = gr.Checkbox(value=False, label="Many faces")
            keep_audio = gr.Checkbox(value=True, label="Keep audio")
            keep_frames = gr.Checkbox(value=False, label="Keep frames")

        video_quality = gr.Slider(minimum=0, maximum=51, value=18, label='Video Quality')

        submit_btn = gr.Button("Submit")

        output_img = gr.Image(type='filepath', label="output image", interactive=False, height=300, visible=True)
        output_video = gr.Video(label="output video", interactive=False, visible=False)

        source_file.change(show_source_file, inputs=source_file, outputs=source_img)
        target_file.change(show_target_file, inputs=[target_file], outputs=[target_img, target_video])

        submit_btn.click(submit_func,
                         inputs=[source_file, target_file, keep_fps, many_face, keep_audio, keep_frames, video_quality],
                         outputs=[output_img, output_video])

    return demo
