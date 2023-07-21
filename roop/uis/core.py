from typing import Callable

import gradio
from roop.uis import control_panel, source_selector, target_selector


def init(start: Callable[[], None]) -> None:
    with gradio.Blocks() as ui:
        control_panel.render(start)
        source_selector.render()
        target_selector.render()

    ui.launch()
