from time import sleep
from typing import Any, Dict, Tuple, List, Optional
import cv2
import gradio

import roop.globals
from roop.capturer import get_video_frame, get_video_frame_total
from roop.core import destroy
from roop.face_analyser import get_one_face
from roop.face_reference import get_face_reference, set_face_reference
from roop.predictor import predict_frame
from roop.processors.frame.core import load_frame_processor_module
from roop.typing import Frame
from roop.uis import core as ui
from roop.uis.typing import ComponentName
from roop.utilities import is_video, is_image

PREVIEW_IMAGE: Optional[gradio.Image] = None
PREVIEW_SLIDER: Optional[gradio.Slider] = None


def render() -> None:
    global PREVIEW_IMAGE
    global PREVIEW_SLIDER

    with gradio.Box():
        preview_image_args: Dict[str, Any] = {
            'label': 'preview_image',
            'visible': False
        }
        preview_slider_args: Dict[str, Any] = {
            'label': 'preview_slider',
            'step': 1,
            'visible': False
        }
        if is_image(roop.globals.target_path):
            temp_frame = cv2.imread(roop.globals.target_path)
            preview_frame = get_preview_frame(temp_frame)
            preview_image_args['value'] = ui.normalize_frame(preview_frame)
            preview_image_args['visible'] = True
        if is_video(roop.globals.target_path):
            temp_frame = get_video_frame(roop.globals.target_path, roop.globals.reference_frame_number)
            preview_frame = get_preview_frame(temp_frame)
            preview_image_args['value'] = ui.normalize_frame(preview_frame)
            preview_image_args['visible'] = True
            preview_slider_args['value'] = roop.globals.reference_frame_number
            preview_slider_args['maximum'] = get_video_frame_total(roop.globals.target_path)
            preview_slider_args['visible'] = True
        PREVIEW_IMAGE = gradio.Image(**preview_image_args)
        PREVIEW_SLIDER = gradio.Slider(**preview_slider_args)
        ui.register_component('preview_slider', PREVIEW_SLIDER)


def listen() -> None:
    PREVIEW_SLIDER.change(update, inputs=PREVIEW_SLIDER, outputs=[PREVIEW_IMAGE, PREVIEW_SLIDER], show_progress=False)
    component_names: List[ComponentName] = [
        'source_file',
        'target_file',
        'reference_face_position_slider',
        'similar_face_distance_slider',
        'frame_processors_checkbox_group',
        'many_faces_checkbox'
    ]
    for component_name in component_names:
        component = ui.get_component(component_name)
        if component:
            component.change(update, inputs=PREVIEW_SLIDER, outputs=[PREVIEW_IMAGE, PREVIEW_SLIDER])


def update(frame_number: int = 0) -> Tuple[Dict[Any, Any], Dict[Any, Any]]:
    sleep(0.5)
    if is_image(roop.globals.target_path):
        temp_frame = cv2.imread(roop.globals.target_path)
        preview_frame = get_preview_frame(temp_frame)
        return gradio.update(value=ui.normalize_frame(preview_frame), visible=True), gradio.update(value=0, maximum=1, visible=False)
    if is_video(roop.globals.target_path):
        roop.globals.reference_frame_number = frame_number
        video_frame_total = get_video_frame_total(roop.globals.target_path)
        temp_frame = get_video_frame(roop.globals.target_path, roop.globals.reference_frame_number)
        preview_frame = get_preview_frame(temp_frame)
        return gradio.update(value=ui.normalize_frame(preview_frame), visible=True), gradio.update(maximum=video_frame_total, visible=True)
    return gradio.update(value=None, visible=False), gradio.update(value=0, maximum=1, visible=False)


def get_preview_frame(temp_frame: Frame) -> Frame:
    if predict_frame(temp_frame):
        destroy()
    source_face = get_one_face(cv2.imread(roop.globals.source_path)) if roop.globals.source_path else None
    if not roop.globals.many_faces and not get_face_reference():
        reference_frame = get_video_frame(roop.globals.target_path, roop.globals.reference_frame_number)
        reference_face = get_one_face(reference_frame, roop.globals.reference_face_position)
        set_face_reference(reference_face)
    reference_face = get_face_reference() if not roop.globals.many_faces else None
    for frame_processor in roop.globals.frame_processors:
        frame_processor_module = load_frame_processor_module(frame_processor)
        if frame_processor_module.pre_start():
            temp_frame = frame_processor_module.process_frame(
                source_face,
                reference_face,
                temp_frame
            )
    return temp_frame


