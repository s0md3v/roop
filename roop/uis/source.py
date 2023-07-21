from typing import Any, Optional, IO
import gradio

import roop.globals
from roop.utilities import is_image

NAME = 'ROOP.UIS.SOURCE'


def render() -> None:
    with gradio.Row():
        source_file = gradio.File(
            file_count='single',
            file_types=['.png', '.jpg', '.jpeg', '.webp'],
            label='source_path'
        )
        source_image = gradio.Image(label='source_image', height=200, visible=False)
        source_file.change(update, inputs=source_file, outputs=source_image)


def update(file: IO[Any]) -> Optional[dict[Any, Any]]:
    if file and is_image(file.name):
        roop.globals.source_path = file.name  # type: ignore
        return gradio.update(value=file.name, visible=True)
    roop.globals.source_path = None
    return gradio.update(value=None, visible=False)
