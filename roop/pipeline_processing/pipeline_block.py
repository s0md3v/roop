import abc

from .environment import PipelineEnvironment


class PipelineBlock(metaclass=abc.ABCMeta):
    """Pipeline block base interface"""

    def __init__(self, environment: PipelineEnvironment) -> None:
        self.environment = environment

    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, 'release') and callable(subclass.release) 
            or NotImplemented
        )

    @abc.abstractmethod
    def release(self) -> None:
        """Release block"""
        pass