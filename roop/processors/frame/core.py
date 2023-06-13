import sys
import importlib
from typing import Any

FRAME_PROCESSOR_MODULE = None


def get_frame_processor_module(frame_processor: str) -> Any:
    global FRAME_PROCESSOR_MODULE

    if not FRAME_PROCESSOR_MODULE:
        try:
            FRAME_PROCESSOR_MODULE = importlib.import_module(f'roop.processors.frame.{frame_processor}')
        except ImportError:
            sys.exit()
    return FRAME_PROCESSOR_MODULE
