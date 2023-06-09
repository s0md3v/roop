from multiprocessing import Lock
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
        self.frame_buffer = []
        self.current_frame = 0

    def collect(self, frame: Frame, lock: Lock = None) -> None:
        if not self.out:
            fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
            self.out = cv2.VideoWriter()
            self.out.open(self.output, fourcc, self.fps, self.size, True)

        self.out.write(frame.data)
        self.current_frame += 1

        """
        # Syncronization
        if lock:
            lock.acquire()

        # Collect frames not 
        if frame.number + 1 != self.current_frame:
            self.frame_buffer.append(frame)
            # Sorting
            self.frame_buffer.sort(key=lambda f: f.number)

        else:
            self.out.write(frame.data)
            self.current_frame += 1
            
            # Save next frames by order
            remove_frames = []
            for buffer_frame in self.frame_buffer:
                if buffer_frame.number + 1 == self.current_frame:
                    remove_frames.append(buffer_frame)
                    self.out.write(frame.data)
                    self.current_frame += 1
                else:
                    break

            # Drop writed frames
            for remove_frame in remove_frames: 
                self.frame_buffer.remove(remove_frame)

            self.current_frame += 1
            
        if lock:
            lock.release()
        """

    def release(self) -> None:
        if self.out:
            self.out.release()