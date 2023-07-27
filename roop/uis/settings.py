from typing import Any, Dict, List
import gradio
import onnxruntime

import roop.globals
from roop.processors.frame.core import clear_frame_processors_modules
from roop.uis import core as ui

NAME = 'ROOP.UIS.OUTPUT'


def render() -> None:
    with gradio.Column():
        with gradio.Box():
            frame_processors_checkbox_group = gradio.CheckboxGroup(
                label='frame_processors',
                choices=['face_swapper', 'face_enhancer'],
                value=roop.globals.frame_processors
            )
            ui.register_component('frame_processors_checkbox_group', frame_processors_checkbox_group)
        with gradio.Box():
            execution_providers_checkbox_group = gradio.CheckboxGroup(
                label='execution_providers',
                choices=onnxruntime.get_available_providers(),
                value=roop.globals.execution_providers
            )
            execution_threads_slider = gradio.Slider(
                label='execution_threads',
                value=roop.globals.execution_threads,
                step=1,
                minimum=1,
                maximum=64
            )
        frame_processors_checkbox_group.change(update_frame_processors, inputs=frame_processors_checkbox_group, outputs=frame_processors_checkbox_group)
        execution_providers_checkbox_group.change(update_execution_providers, inputs=execution_providers_checkbox_group, outputs=execution_providers_checkbox_group)
        execution_threads_slider.change(update_execution_threads, inputs=execution_threads_slider, outputs=execution_threads_slider)


def update_frame_processors(frame_processors: List[str]) -> Dict[Any, Any]:
    clear_frame_processors_modules()
    roop.globals.frame_processors = frame_processors
    return gradio.update(value=frame_processors)


def update_execution_providers(execution_providers: List[str]) -> Dict[Any, Any]:
    roop.globals.execution_providers = execution_providers
    return gradio.update(value=execution_providers)


def update_execution_threads(execution_threads: int = 1) -> Dict[Any, Any]:
    roop.globals.execution_threads = execution_threads
    return gradio.update(value=execution_threads)
