import abc
from typing import Any

from ..common import Frame
from ..pipeline_block import PipelineBlock


class ProcessBlock(PipelineBlock):
    """Pipeline process block base interface"""

    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, 'init') and callable(subclass.init) 
            and hasattr(subclass, 'process') and callable(subclass.process) 
            or NotImplemented
        )

    @abc.abstractmethod
    def init(self, face: str) -> Any:
        """Init process block"""
        pass

    @abc.abstractmethod
    def process(self, frame: Frame) -> Frame:
        """Process frame"""
        pass