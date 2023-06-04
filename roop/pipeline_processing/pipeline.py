import abc
from typing import Any, Callable, List, Tuple

from tqdm import tqdm

from roop.pipeline_processing.environment import PipelineEnvironment

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


class PipelineProcessBlock(PipelineBlock):
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
    def process(self, frame: Any) -> Any:
        """Process frame"""
        pass


class FramesExtractor(PipelineBlock):
    """Frame extractor base interface"""

    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, 'next') and callable(subclass.next)
            and hasattr(subclass, 'frame') and callable(subclass.frame) 
            or NotImplemented
        )

    def init(self, input: str) -> None:
        """Bind input file"""
        self.input = input
        self.cap = None
        self.current_frame = 0

    @abc.abstractmethod
    def info(self) -> Tuple[Tuple[int, int], int, int]:
        """Return input info: ((width, height), fps, frames_count)"""
        pass

    @abc.abstractmethod
    def next(self) -> Tuple[bool, Any]:
        """Get next frame"""
        pass
    
    @abc.abstractmethod
    def frame(self, num: int) -> Any | None:
        """Get frame by name"""
        pass


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
    def collect(self, frame: Any) -> None:
        """Collect frame"""
        pass  


class Postprocess(PipelineBlock):
    """Postprocess block interface"""

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
    def process(self, input: str, output: str) -> None:
        """Process data"""
        pass  


class CancellationToken:
    """Cancellation token"""

    def __init__(self):
        self.cancelled = False

    def cancel(self):
        """Set cancelled"""
        self.cancelled = True


class PipelineExecutionParams():
    """Pipeline execution params"""

    def __init__(
            self,
            face: str,
            target: str, 
            output: str,
            progress_handler: Callable[[str], None] = None,
            preview_handler: Callable[[Any], None] = None
        ):
        self.face = face
        self.target = target
        self.output = output
        self.preview_handler = preview_handler
        self.progress_handler = progress_handler


class Pipeline:
    def __init__(
            self, 
            extractor: FramesExtractor, 
            blocks: List[PipelineProcessBlock],
            collector: FramesCollector,
            postprocess: Postprocess
        ):
        self.extractor = extractor
        self.blocks = blocks
        self.collector = collector
        self.postprocess = postprocess

    def execute(
            self,
            params: PipelineExecutionParams, 
            cancellation_token: CancellationToken
        ):
        """Main execution method"""
        params.progress_handler("Init blocks")

        # Init blocks
        self.extractor.init(params.target)
        for block in self.blocks:
            block.init(params.face)
        size, fps, frames_count = self.extractor.info()
        self.collector.init(params.output, fps, size)

        params.progress_handler("Start processing...")
        
        progress_bar_format = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'

        with tqdm(total=frames_count, desc="Processing", unit="frame", dynamic_ncols=True, bar_format=progress_bar_format) as progress:
            # Frame processing
            ret, frame = self.extractor.next()
            while ret:
                for block in self.blocks:
                    frame = block.process(frame)
                self.collector.collect(frame)

                if params.progress_handler:
                    params.progress_handler(self.extractor.current_frame)
                if params.preview_handler:
                    params.preview_handler(frame)
                
                # Cancelling process
                if cancellation_token.cancelled:
                    break
                
                progress.update(1)
                ret, frame = self.extractor.next()
        
        params.progress_handler("Process finished.")
        self.extractor.release()
        self.collector.release()

        params.progress_handler("Postprocessing...")
        self.postprocess.process(params.target, params.output)
        params.progress_handler("Postprocessing finished.")

    def release(self):
        """Release resources"""
        self.extractor.release()
        for block in self.blocks:
            block.release()
        self.collector.release()