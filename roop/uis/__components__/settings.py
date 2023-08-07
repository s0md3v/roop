from typing import Any, Dict, List, Optional
import gradio
import onnxruntime

import roop.globals
from roop.processors.frame.core import list_frame_processors_names, load_frame_processor_module, clear_frame_processors_modules
from roop.uis import core as ui

FRAME_PROCESSORS_CHECKBOX_GROUP: Optional[gradio.CheckboxGroup] = None
EXECUTION_PROVIDERS_CHECKBOX_GROUP: Optional[gradio.CheckboxGroup] = None
EXECUTION_THREADS_SLIDER: Optional[gradio.Slider] = None
KEEP_FPS_CHECKBOX: Optional[gradio.Checkbox] = None
KEEP_TEMP_CHECKBOX: Optional[gradio.Checkbox] = None
SKIP_AUDIO_CHECKBOX: Optional[gradio.Checkbox] = None
MANY_FACES_CHECKBOX: Optional[gradio.Checkbox] = None


def render() -> None:
    global FRAME_PROCESSORS_CHECKBOX_GROUP
    global EXECUTION_PROVIDERS_CHECKBOX_GROUP
    global EXECUTION_THREADS_SLIDER
    global KEEP_FPS_CHECKBOX
    global KEEP_TEMP_CHECKBOX
    global SKIP_AUDIO_CHECKBOX
    global MANY_FACES_CHECKBOX

    with gradio.Column():
        with gradio.Box():
            FRAME_PROCESSORS_CHECKBOX_GROUP = gradio.CheckboxGroup(
                label='frame_processors',
                choices=sort_frame_processors(roop.globals.frame_processors),
                value=roop.globals.frame_processors
            )
            ui.register_component('frame_processors_checkbox_group', FRAME_PROCESSORS_CHECKBOX_GROUP)
        with gradio.Box():
            EXECUTION_PROVIDERS_CHECKBOX_GROUP = gradio.CheckboxGroup(
                label='execution_providers',
                choices=onnxruntime.get_available_providers(),
                value=roop.globals.execution_providers
            )
            EXECUTION_THREADS_SLIDER = gradio.Slider(
                label='execution_threads',
                value=roop.globals.execution_threads,
                step=1,
                minimum=1,
                maximum=64
            )
        with gradio.Box():
            KEEP_FPS_CHECKBOX = gradio.Checkbox(
                label='keep_fps',
                value=roop.globals.keep_fps
            )
            KEEP_TEMP_CHECKBOX = gradio.Checkbox(
                label='keep_temp',
                value=roop.globals.keep_fps
            )
            SKIP_AUDIO_CHECKBOX = gradio.Checkbox(
                label='skip_audio',
                value=roop.globals.skip_audio
            )
            MANY_FACES_CHECKBOX = gradio.Checkbox(
                label='many_faces',
                value=roop.globals.many_faces
            )
            ui.register_component('many_faces_checkbox', MANY_FACES_CHECKBOX)


def listen() -> None:
    FRAME_PROCESSORS_CHECKBOX_GROUP.change(update_frame_processors, inputs=FRAME_PROCESSORS_CHECKBOX_GROUP, outputs=FRAME_PROCESSORS_CHECKBOX_GROUP)
    EXECUTION_PROVIDERS_CHECKBOX_GROUP.change(update_execution_providers, inputs=EXECUTION_PROVIDERS_CHECKBOX_GROUP, outputs=EXECUTION_PROVIDERS_CHECKBOX_GROUP)
    EXECUTION_THREADS_SLIDER.change(update_execution_threads, inputs=EXECUTION_THREADS_SLIDER, outputs=EXECUTION_THREADS_SLIDER)
    KEEP_FPS_CHECKBOX.change(lambda value: update_checkbox('keep_fps', value), inputs=KEEP_FPS_CHECKBOX, outputs=KEEP_FPS_CHECKBOX)
    KEEP_TEMP_CHECKBOX.change(lambda value: update_checkbox('keep_temp', value), inputs=KEEP_TEMP_CHECKBOX, outputs=KEEP_TEMP_CHECKBOX)
    SKIP_AUDIO_CHECKBOX.change(lambda value: update_checkbox('skip_audio', value), inputs=SKIP_AUDIO_CHECKBOX, outputs=SKIP_AUDIO_CHECKBOX)
    MANY_FACES_CHECKBOX.change(lambda value: update_checkbox('many_faces', value), inputs=MANY_FACES_CHECKBOX, outputs=MANY_FACES_CHECKBOX)


def update_frame_processors(frame_processors: List[str]) -> Dict[Any, Any]:
    clear_frame_processors_modules()
    roop.globals.frame_processors = frame_processors
    for frame_processor in roop.globals.frame_processors:
        frame_processor_module = load_frame_processor_module(frame_processor)
        frame_processor_module.pre_check()
    return gradio.update(value=frame_processors, choices=sort_frame_processors(frame_processors))


def sort_frame_processors(frame_processors: List[str]) -> list[str]:
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
