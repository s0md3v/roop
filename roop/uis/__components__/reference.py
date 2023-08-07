from typing import Dict, Any, List, Optional
from time import sleep

import cv2
import gradio

import roop.globals
from roop.capturer import get_video_frame
from roop.face_analyser import get_faces_total
from roop.face_reference import clear_face_reference
from roop.uis import core as ui
from roop.uis.typing import ComponentName
from roop.utilities import is_image, is_video

REFERENCE_FACE_POSITION_SLIDER: Optional[gradio.Slider] = None
SIMILAR_FACE_DISTANCE_SLIDER: Optional[gradio.Slider] = None


def render() -> None:
    global REFERENCE_FACE_POSITION_SLIDER
    global SIMILAR_FACE_DISTANCE_SLIDER

    with gradio.Box():
        reference_face_position_slider_args = {
            'label': 'reference_face_position',
            'value': roop.globals.reference_face_position,
            'step': 1,
            'maximum': 0
        }
        if is_image(roop.globals.target_path):
            target_frame = cv2.imread(roop.globals.target_path)
            reference_face_position_slider_args['maximum'] = get_faces_total(target_frame)
        if is_video(roop.globals.target_path):
            target_frame = get_video_frame(roop.globals.target_path, roop.globals.reference_frame_number)
            reference_face_position_slider_args['maximum'] = get_faces_total(target_frame)
        REFERENCE_FACE_POSITION_SLIDER = gradio.Slider(**reference_face_position_slider_args)
        SIMILAR_FACE_DISTANCE_SLIDER = gradio.Slider(
            label='similar_face_distance',
            value=roop.globals.similar_face_distance,
            maximum=2,
            step=0.05
        )
        ui.register_component('reference_face_position_slider', REFERENCE_FACE_POSITION_SLIDER)
        ui.register_component('similar_face_distance_slider', SIMILAR_FACE_DISTANCE_SLIDER)


def listen() -> None:
    SIMILAR_FACE_DISTANCE_SLIDER.change(update_similar_face_distance, inputs=SIMILAR_FACE_DISTANCE_SLIDER)
    component_names: List[ComponentName] = [
        'target_file',
        'preview_slider'
    ]
    for component_name in component_names:
        component = ui.get_component(component_name)
        if component:
            component.change(update_face_reference_position, inputs=REFERENCE_FACE_POSITION_SLIDER, outputs=REFERENCE_FACE_POSITION_SLIDER)
    REFERENCE_FACE_POSITION_SLIDER.change(clear_and_update_face_reference_position, inputs=REFERENCE_FACE_POSITION_SLIDER)


def clear_and_update_face_reference_position(reference_face_position: int) -> Dict[Any, Any]:
    clear_face_reference()
    return update_face_reference_position(reference_face_position)


def update_face_reference_position(reference_face_position: int) -> Dict[Any, Any]:
    sleep(0.5)
    maximum = 0
    roop.globals.reference_face_position = reference_face_position
    if is_image(roop.globals.target_path):
        target_frame = cv2.imread(roop.globals.target_path)
        maximum = get_faces_total(target_frame)
    if is_video(roop.globals.target_path):
        target_frame = get_video_frame(roop.globals.target_path, roop.globals.reference_frame_number)
        maximum = get_faces_total(target_frame)
    return gradio.update(value=reference_face_position, maximum=maximum)


def update_similar_face_distance(similar_face_distance: float) -> Dict[Any, Any]:
    roop.globals.similar_face_distance = similar_face_distance
    return gradio.update(value=similar_face_distance)
