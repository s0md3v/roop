from typing import Any, Optional

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
from roop.uis.source import get_source_file
from roop.utilities import is_video

NAME = 'ROOP.UIS.PREVIEW'
PREVIEW_IMAGE = None
PREVIEW_SLIDER = None


def render() -> None:
    with gradio.Column():
        is_target_video = is_video(roop.globals.target_path)
        preview_image = get_preview_image()
        if is_target_video:
            preview_slider = get_preview_slider()
            preview_slider.change(update_preview_image, inputs=preview_slider, outputs=preview_image, show_progress=False)
        # get_source_file().change(update_preview_image, inputs=preview_slider, outputs=preview_image, show_progress=False)
        # get_source_file().clear(clear, outputs=preview_image, show_progress=False)


def get_preview_image() -> gradio.Image:
    global PREVIEW_IMAGE

    if PREVIEW_IMAGE is None:
        is_target_video = is_video(roop.globals.target_path)
        PREVIEW_IMAGE = gradio.Image(
            label='preview_image',
            value=normalize_preview_frame(get_preview_frame(roop.globals.reference_frame_number)) if is_target_video else None
        )
    return PREVIEW_IMAGE


def get_preview_slider() -> gradio.Slider:
    global PREVIEW_SLIDER

    if PREVIEW_SLIDER is None:
        video_frame_total = get_video_frame_total(roop.globals.target_path)
        PREVIEW_SLIDER = gradio.Slider(
            label='preview_slider',
            value=roop.globals.reference_frame_number,
            maximum=video_frame_total
        )
    return PREVIEW_SLIDER


def update_preview_image(frame_number: int = 0) -> Optional[dict[Any, Any]]:
    preview_frame = get_preview_frame(frame_number)
    if preview_frame.any():
        return gradio.update(value=normalize_preview_frame(preview_frame))
    return gradio.update(value=None)


def get_preview_frame(frame_number: int = 0) -> Frame:
    temp_frame = get_video_frame(roop.globals.target_path, frame_number)
    if predict_frame(temp_frame):
        destroy()
    source_face = get_one_face(cv2.imread(roop.globals.source_path))
    if not get_face_reference():
        reference_frame = get_video_frame(roop.globals.target_path, roop.globals.reference_frame_number)
        reference_face = get_one_face(reference_frame, roop.globals.reference_face_position)
        set_face_reference(reference_face)
    else:
        reference_face = get_face_reference()
    for frame_processor in get_frame_processors_modules(roop.globals.frame_processors):
        temp_frame = frame_processor.process_frame(
            source_face,
            reference_face,
            temp_frame
        )
    return temp_frame


def normalize_preview_frame(preview_frame: Frame) -> Frame:
    return cv2.cvtColor(preview_frame, cv2.COLOR_BGR2RGB)
