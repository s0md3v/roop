from typing import Any, Dict, IO, Optional
import gradio

import roop.globals
from roop.uis import core as ui
from roop.utilities import is_image

SOURCE_FILE: Optional[gradio.File] = None
SOURCE_IMAGE: Optional[gradio.Image] = None


def render() -> None:
    global SOURCE_FILE
    global SOURCE_IMAGE

    with gradio.Box():
        is_source_image = is_image(roop.globals.source_path)
        SOURCE_FILE = gradio.File(
            file_count='single',
            file_types=['.png', '.jpg', '.jpeg', '.webp'],
            label='source_path',
            value=roop.globals.source_path if is_source_image else None
        )
        ui.register_component('source_file', SOURCE_FILE)
        SOURCE_IMAGE = gradio.Image(
            label='source_image',
            value=SOURCE_FILE.value['name'] if is_source_image else None,
            visible=is_source_image
        )


def listen() -> None:
    SOURCE_FILE.change(update, inputs=SOURCE_FILE, outputs=SOURCE_IMAGE)


def update(file: IO[Any]) -> Dict[str, Any]:
    if file and is_image(file.name):
        roop.globals.source_path = file.name
        return gradio.update(value=file.name, visible=True)
    roop.globals.source_path = None
    return gradio.update(value=None, visible=False)
