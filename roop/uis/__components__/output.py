from typing import Any, Dict, Tuple
import gradio

import roop.globals
from roop.core import start
from roop.utilities import has_image_extension, has_video_extension, normalize_output_path


def render() -> None:
    with gradio.Column():
        with gradio.Row():
            start_button = gradio.Button('Start')
            clear_button = gradio.Button('Clear')
        output_image = gradio.Image(label='output_image', visible=False)
        output_video = gradio.Video(label='output_video', visible=False)
        start_button.click(update, outputs=[output_image, output_video])
        clear_button.click(clear, outputs=[output_image, output_video])


def update() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    roop.globals.output_path = normalize_output_path(roop.globals.source_path, roop.globals.target_path, '..')
    if roop.globals.output_path:
        start()
        if has_image_extension(roop.globals.output_path):
            return gradio.update(value=roop.globals.output_path, visible=True), gradio.update(value=None, visible=False)
        if has_video_extension(roop.globals.output_path):
            return gradio.update(value=None, visible=False), gradio.update(value=roop.globals.output_path, visible=True)
    return gradio.update(value=None, visible=False), gradio.update(value=None, visible=False)


def clear() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    return gradio.update(value=None, visible=False), gradio.update(value=None, visible=False)
