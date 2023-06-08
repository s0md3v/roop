from typing import Any


class Frame:
    """Frame data with meta"""

    def __init__(self, frame: Any, number: int) -> None:
        self.data = frame
        self.number = number