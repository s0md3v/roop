import abc
from typing import Tuple

from ..common import Frame
from ..pipeline_block import PipelineBlock


class FramesCollector(PipelineBlock):
    """Frames collector base interface"""

    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, 'init') and callable(subclass.init) 
            and hasattr(subclass, 'collect') and callable(subclass.collect) 
            or NotImplemented
        )

    def init(self, output: str, fps: int, size: Tuple[int, int]) -> None:
        """Init frames collector"""
        pass

    @abc.abstractmethod
    def collect(self, frame: Frame) -> None:
        """Collect frame"""
        pass  
