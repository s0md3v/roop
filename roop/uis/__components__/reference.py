from time import sleep
from typing import Dict, Any

import gradio

import roop.globals
from roop.capturer import get_video_frame
from roop.face_analyser import get_many_faces
from roop.uis import core as ui
from roop.utilities import is_video


def render() -> None:
    with gradio.Box():
        reference_face_gallery_args: Dict[str, Any] = {
            'label': 'reference_faces',
            'columns': 6,
            'height': 200,
            'allow_preview': False,
            'visible': True
        }
        if is_video(roop.globals.target_path):
            target_frame = get_video_frame(roop.globals.target_path, roop.globals.reference_frame_number)
            faces = get_many_faces(target_frame)
            if faces:
                value = []
                for face in faces:
                    start_x, start_y, end_x, end_y = map(int, face['bbox'])
                    crop_frame = target_frame[start_y:end_y, start_x:end_x]
                    value.append(ui.normalize_frame(crop_frame))
                reference_face_gallery_args['value'] = value
            else:
                reference_face_gallery_args['value'] = []
        reference_face_gallery = gradio.Gallery(**reference_face_gallery_args)
        similar_face_distance_slider = gradio.Slider(
            label='similar_face_distance',
            value=roop.globals.similar_face_distance,
            minimum=0,
            maximum=2,
            step=0.05
        )
        ui.register_component('reference_face_gallery', reference_face_gallery)
