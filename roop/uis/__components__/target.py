from typing import Any, Dict, IO, Tuple, Optional
import gradio

import roop.globals
from roop.face_reference import clear_face_reference
from roop.uis import core as ui
from roop.utilities import is_image, is_video

TARGET_FILE: Optional[gradio.File] = None
TARGET_IMAGE: Optional[gradio.Image] = None
TARGET_VIDEO: Optional[gradio.Video] = None


def render() -> None:
    global TARGET_FILE
    global TARGET_IMAGE
    global TARGET_VIDEO

    with gradio.Box():
        is_target_image = is_image(roop.globals.target_path)
        is_target_video = is_video(roop.globals.target_path)
        TARGET_FILE = gradio.File(
            file_count='single',
            file_types=['.png', '.jpg', '.jpeg', '.webp', '.mp4'],
            label='target_path',
            value=roop.globals.target_path if is_target_image or is_target_video else None
        )
        ui.register_component('target_file', TARGET_FILE)
        TARGET_IMAGE = gradio.Image(
            label='target_image',
            value=TARGET_FILE.value['name'] if is_target_image else None,
            visible=is_target_image
        )
        TARGET_VIDEO = gradio.Video(
            label='target_video',
            value=TARGET_FILE.value['name'] if is_target_video else None,
            visible=is_target_video
        )


def listen() -> None:
    TARGET_FILE.change(update, inputs=TARGET_FILE, outputs=[TARGET_IMAGE, TARGET_VIDEO])


def update(file: IO[Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    clear_face_reference()
    if file and is_image(file.name):
        roop.globals.target_path = file.name
        return gradio.update(value=file.name, visible=True), gradio.update(value=None, visible=False)
    if file and is_video(file.name):
        roop.globals.target_path = file.name
        return gradio.update(value=None, visible=False), gradio.update(value=file.name, visible=True)
    roop.globals.target_path = None
    return gradio.update(value=None, visible=False), gradio.update(value=None, visible=False)
