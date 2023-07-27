from typing import Any, Dict, List
import gradio
import onnxruntime

import roop.globals

NAME = 'ROOP.UIS.OUTPUT'


def render() -> None:
    with gradio.Row():
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
        execution_providers_checkbox_group.change(update_execution_providers, inputs=execution_providers_checkbox_group, outputs=execution_providers_checkbox_group)
        execution_threads_slider.change(update_execution_threads, inputs=execution_threads_slider, outputs=execution_threads_slider)


def update_execution_providers(execution_providers: List[str]) -> Dict[Any, Any]:
    roop.globals.execution_providers = execution_providers
    return gradio.update(value=execution_providers)


def update_execution_threads(execution_threads: int = 1) -> Dict[Any, Any]:
    roop.globals.execution_threads = execution_threads
    return gradio.update(value=execution_threads)
