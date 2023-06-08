from typing import Tuple

import cv2

from ..common import Frame
from ..collectors import FramesCollector


class BasicCollector(FramesCollector):
    """Basic video collector"""

    def init(self, output: str, fps: int, size: Tuple[int, int]) -> None:
        """Bind output file"""
        self.output = output
        self.out = None
        self.fps = fps
        self.size = size
        self.current_frame = 0

    def collect(self, frame: Frame) -> None:
        if not self.out:
            fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
            self.out = cv2.VideoWriter()
            self.out.open(self.output, fourcc, self.fps, self.size, True)

        self.out.write(frame.data)
        self.current_frame += 1

    def release(self) -> None:
        if self.out:
            self.out.release()