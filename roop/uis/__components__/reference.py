from time import sleep
from typing import Dict, Any

import gradio
import numpy

import roop.globals
from roop.capturer import get_video_frame
from roop.face_analyser import get_many_faces
from roop.face_reference import clear_face_reference
from roop.uis import core as ui
from roop.utilities import is_video


def render() -> None:
    with gradio.Box():
        if is_video(roop.globals.target_path):
            target_frame = get_video_frame(roop.globals.target_path, roop.globals.reference_frame_number)
            faces = get_many_faces(target_frame)
        reference_face_position_slider = gradio.Slider(
            label='reference_face_position',
            value=roop.globals.reference_face_position,
            maximum=len(faces),
            step=1
        )
        ui.register_component('reference_face_position_slider', reference_face_position_slider)
        similar_face_distance_slider = gradio.Slider(
            label='similar_face_distance',
            value=roop.globals.similar_face_distance,
            maximum=2,
            step=0.05
        )
        ui.register_component('similar_face_distance_slider', reference_face_position_slider)
        reference_face_position_slider.change(update_face_reference_position, inputs=reference_face_position_slider)
        similar_face_distance_slider.change(update_similar_face_distance, inputs=similar_face_distance_slider)


def update_face_reference_position(reference_face_position: int) -> Dict[Any, Any]:
    clear_face_reference()
    roop.globals.reference_face_position = reference_face_position
    return gradio.update(value=reference_face_position)


def update_similar_face_distance(similar_face_distance: float) -> Dict[Any, Any]:
    roop.globals.similar_face_distance = similar_face_distance
    return gradio.update(value=similar_face_distance)
