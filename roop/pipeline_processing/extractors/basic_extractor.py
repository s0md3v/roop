from typing import Any
import cv2

from roop.pipeline_processing.pipeline import FramesExtractor

class BasicExtractor(FramesExtractor):
    """Basic video extractor"""

    def info(self):
        if not self.input:
            return
        
        cap = cv2.VideoCapture(self.input)

        if not cap.isOpened():
            print("Error opening video file")
            return

        # Get height, width and frame count of the video
        self.width, self.height = (
                int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            )
        self.fps = int(cap.get(cv2.CAP_PROP_FPS))
        self.frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        
        cap.release()
        
        return ((self.width, self.height), self.fps, self.frame_count)
    
    def next(self):
        if not self.input:
            return (False, None)

        if not self.cap:
            self.cap = cv2.VideoCapture(self.input)

        ret, frame = self.cap.read()
        if not ret:
            self.current_frame = 0
            self.cap.release()
            return (False, None)
        
        self.current_frame += 1       
        return (True, frame)

    # TODO
    def frame(self, num: int) -> Any | None:
        pass

    def release(self) -> None:
        if self.cap:
            self.cap.release()