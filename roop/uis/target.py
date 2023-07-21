from typing import Any, Optional, IO

import gradio

import roop.globals
from roop.utilities import is_image, is_video

NAME = 'ROOP.UIS.TARGET'


def render() -> None:
    with gradio.Row():
        target_file = gradio.File(
            file_count='single',
            file_types=['.png', '.jpg', '.jpeg', '.webp', '.mp4'],
            label='target_path'
        )
        target_image = gradio.Image(label='target_image', interactive=False, height=200, width=200, visible=False)
        target_video = gradio.Video(label='target_video', interactive=False, height=200, width=200, visible=False)
        target_file.change(update, inputs=target_file, outputs=[target_image, target_video])


def update(file: IO[Any]) -> Optional[tuple[dict[str, Any], dict[str, Any]]]:
    if file and is_image(file.name):
        roop.globals.target_path = file.name  # type: ignore
        return gradio.update(value=file.name, visible=True), gradio.update(value=None, visible=False)
    if file and is_video(file.name):
        roop.globals.target_path = file.name  # type: ignore
        return gradio.update(value=None, visible=False), gradio.update(value=file.name, visible=True)
    return gradio.update(value=None, visible=False), gradio.update(value=None, visible=False)
