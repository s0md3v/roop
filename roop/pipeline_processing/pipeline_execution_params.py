from typing import Any, Callable


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
