from typing import Any

from ..process_blocks import ProcessBlock


class Dummy(ProcessBlock):
    """Dummy process block, returns input frame"""

    def init(self, face: str) -> Any:
        pass

    def process(self, frame: Any) -> Any:
        return frame
    
    def release(self) -> None:
        pass