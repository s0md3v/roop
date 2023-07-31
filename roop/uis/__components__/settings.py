from typing import Any, Dict, List
import gradio
import onnxruntime

import roop.globals
from roop.processors.frame.core import list_frame_processors_names, clear_frame_processors_modules
from roop.uis import core as ui


def render() -> None:
    with gradio.Column():
        with gradio.Box():
            frame_processors_checkbox_group = gradio.CheckboxGroup(
                label='frame_processors',
                choices=sort_frame_processors(roop.globals.frame_processors),
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
        with gradio.Box():
            keep_fps_checkbox = gradio.Checkbox(
                label='keep_fps',
                value=roop.globals.keep_fps
            )
            keep_temp_checkbox = gradio.Checkbox(
                label='keep_temp',
                value=roop.globals.keep_fps
            )
            skip_audio_checkbox = gradio.Checkbox(
                label='skip_audio',
                value=roop.globals.skip_audio
            )
            many_faces_checkbox = gradio.Checkbox(
                label='many_faces',
                value=roop.globals.many_faces
            )
            ui.register_component('many_faces_checkbox', many_faces_checkbox)

        frame_processors_checkbox_group.change(update_frame_processors, inputs=frame_processors_checkbox_group, outputs=frame_processors_checkbox_group)
        execution_providers_checkbox_group.change(update_execution_providers, inputs=execution_providers_checkbox_group, outputs=execution_providers_checkbox_group)
        execution_threads_slider.change(update_execution_threads, inputs=execution_threads_slider, outputs=execution_threads_slider)
        keep_fps_checkbox.change(lambda value: update_checkbox('keep_fps', value), inputs=keep_fps_checkbox, outputs=keep_fps_checkbox)
        keep_temp_checkbox.change(lambda value: update_checkbox('keep_temp', value), inputs=keep_temp_checkbox, outputs=keep_temp_checkbox)
        skip_audio_checkbox.change(lambda value: update_checkbox('skip_audio', value), inputs=skip_audio_checkbox, outputs=skip_audio_checkbox)
        many_faces_checkbox.change(lambda value: update_checkbox('many_faces', value), inputs=many_faces_checkbox, outputs=many_faces_checkbox)


def update_frame_processors(frame_processors: List[str]) -> Dict[Any, Any]:
    clear_frame_processors_modules()
    roop.globals.frame_processors = frame_processors
    return gradio.update(value=frame_processors, choices=sort_frame_processors(frame_processors))


def sort_frame_processors(frame_processors: List[str]):
    frame_processor_key = lambda frame_processor: frame_processors.index(frame_processor) if frame_processor in frame_processors else len(frame_processors)
    return sorted(list_frame_processors_names(), key=frame_processor_key)


def update_execution_providers(execution_providers: List[str]) -> Dict[Any, Any]:
    roop.globals.execution_providers = execution_providers
    return gradio.update(value=execution_providers)


def update_execution_threads(execution_threads: int = 1) -> Dict[Any, Any]:
    roop.globals.execution_threads = execution_threads
    return gradio.update(value=execution_threads)


def update_checkbox(name: str, value: bool) -> Dict[Any, Any]:
    setattr(roop.globals, name, value)
    return gradio.update(value=value)
