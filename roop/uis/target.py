from typing import Any, Optional, IO
import gradio

import roop.globals
from roop.utilities import is_image, is_video

NAME = 'ROOP.UIS.TARGET'


def render() -> None:
    with gradio.Column():
        is_target_image = is_image(roop.globals.target_path)
        is_target_video = is_video(roop.globals.target_path)
        target_file = gradio.File(
            file_count='single',
            file_types=['.png', '.jpg', '.jpeg', '.webp', '.mp4'],
            label='target_path',
            value=roop.globals.target_path if is_target_image or is_target_video else None
        )
        target_image = gradio.Image(
            label='target_image',
            value=target_file.value['name'] if is_target_image else None,
            height=200,
            visible=is_target_image
        )
        target_video = gradio.Video(
            label='target_video',
            value=target_file.value['name'] if is_target_video else None,
            height=200,
            visible=is_target_video
        )
        target_file.change(update, inputs=target_file, outputs=[target_image, target_video])


def update(file: IO[Any]) -> Optional[tuple[dict[str, Any], dict[str, Any]]]:
    if file and is_image(file.name):
        roop.globals.target_path = file.name  # type: ignore
        return gradio.update(value=file.name, visible=True), gradio.update(value=None, visible=False)
    if file and is_video(file.name):
        roop.globals.target_path = file.name  # type: ignore
        return gradio.update(value=None, visible=False), gradio.update(value=file.name, visible=True)
    roop.globals.target_path = None
    return gradio.update(value=None, visible=False), gradio.update(value=None, visible=False)
