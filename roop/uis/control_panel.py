from typing import Callable
import gradio

import roop.globals

NAME = 'ROOP.CONTROL_PANEL'


def render(start: Callable[[], None]) -> None:
    roop.globals.output_path = '.'
    with gradio.Row():
        start_button = gradio.Button('Start')
        start_button.click(start)
