from typing import Any

from roop.pipeline_processing.pipeline import PipelineProcessBlock


class Dummy(PipelineProcessBlock):
    """Dummy process block, returns input frame"""

    def init(self, face: str) -> Any:
        pass

    def process(self, frame: Any) -> Any:
        return frame
    
    def release(self) -> None:
        pass