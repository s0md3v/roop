from typing import Any
import cv2


def get_video_frame(video_path: str, frame_number: int = 1) -> Any:
    capture = cv2.VideoCapture(video_path)
    frame_total = capture.get(cv2.CAP_PROP_FRAME_COUNT)
    capture.set(cv2.CAP_PROP_POS_FRAMES, min(frame_total, frame_number - 1))
    has_frame, frame = capture.read()
    capture.release()
    if has_frame:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return None
