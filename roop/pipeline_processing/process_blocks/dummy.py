from typing import Any

from ..common import Frame
from ..process_blocks import ProcessBlock


class Dummy(ProcessBlock):
    """Dummy process block, returns input frame"""

    def init(self, face: str) -> Any:
        pass

    def process(self, frame: Frame) -> Any:
        return frame
    
    def release(self) -> None:
        pass