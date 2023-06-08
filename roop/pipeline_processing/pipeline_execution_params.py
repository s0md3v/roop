from typing import Any, Callable

from .common import Frame


class PipelineExecutionParams():
    """Pipeline execution params"""

    def __init__(
            self,
            face: str,
            target: str, 
            output: str,
            progress_handler: Callable[[str], None] = None,
            preview_handler: Callable[[Frame], None] = None
        ):
        self.face = face
        self.target = target
        self.output = output
        self.preview_handler = preview_handler
        self.progress_handler = progress_handler
