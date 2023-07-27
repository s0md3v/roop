from time import sleep
from typing import Any, Dict, Tuple
import cv2
import gradio

import roop.globals
from roop.capturer import get_video_frame, get_video_frame_total
from roop.core import destroy
from roop.face_analyser import get_one_face
from roop.face_reference import get_face_reference, set_face_reference
from roop.predictor import predict_frame
from roop.processors.frame.core import get_frame_processors_modules
from roop.typing import Frame
from roop.uis import core as ui
from roop.utilities import is_video, is_image

NAME = 'ROOP.UIS.PREVIEW'


def render() -> None:
    with gradio.Column():
        is_target_image = is_image(roop.globals.target_path)
        is_target_video = is_video(roop.globals.target_path)
        if is_target_image:
            temp_frame = cv2.imread(roop.globals.target_path)
        if is_target_video:
            video_frame_total = get_video_frame_total(roop.globals.target_path)
            temp_frame = get_video_frame(roop.globals.target_path, roop.globals.reference_frame_number)
        preview_frame = get_preview_frame(temp_frame)
        preview_image = gradio.Image(
            label='preview_image',
            value=normalize_preview_frame(preview_frame),
            height=400,
            visible=is_target_image or is_target_video
        )
        preview_slider = gradio.Slider(
            label='preview_slider',
            value=roop.globals.reference_frame_number if is_target_video else 0,
            maximum=video_frame_total if is_target_video else 1,
            visible=is_target_video
        )
        preview_slider.change(update, inputs=preview_slider, outputs=[preview_image, preview_slider], show_progress=False)
        source_file = ui.get_component('source_file')
        target_file = ui.get_component('target_file')
        if source_file:
            source_file.change(update, inputs=preview_slider, outputs=[preview_image, preview_slider])
        if target_file:
            target_file.change(update, inputs=preview_slider, outputs=[preview_image, preview_slider])


def update(frame_number: int = 0) -> Tuple[Dict[Any, Any], Dict[Any, Any]]:
    sleep(0.1)
    if is_image(roop.globals.target_path):
        temp_frame = cv2.imread(roop.globals.target_path)
        preview_frame = get_preview_frame(temp_frame)
        if preview_frame.any():
            return gradio.update(value=normalize_preview_frame(preview_frame), visible=True), gradio.update(value=0, maximum=1, visible=False)
    if is_video(roop.globals.target_path):
        video_frame_total = get_video_frame_total(roop.globals.target_path)
        temp_frame = get_video_frame(roop.globals.target_path, frame_number)
        preview_frame = get_preview_frame(temp_frame)
        if preview_frame.any():
            return gradio.update(value=normalize_preview_frame(preview_frame), visible=True), gradio.update(value=frame_number, maximum=video_frame_total, visible=True)
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
    for frame_processor in get_frame_processors_modules(roop.globals.frame_processors):
        if frame_processor.pre_start():
            temp_frame = frame_processor.process_frame(
                source_face,
                reference_face,
                temp_frame
            )
    return temp_frame


def normalize_preview_frame(preview_frame: Frame) -> Frame:
    return cv2.cvtColor(preview_frame, cv2.COLOR_BGR2RGB)
