import sys
import importlib
from typing import Any

FRAME_PROCESSORS_MODULES = None

def load_processor_module(frame_processor: str)-> Any:
    try:
        frame_processor_module = importlib.import_module(f'roop.processors.frame.{frame_processor}')
    except ImportError:
        sys.exit()
    return frame_processor_module


def get_frame_processors_modules(frame_processors):
    global FRAME_PROCESSORS_MODULES
    if FRAME_PROCESSORS_MODULES is None:
        FRAME_PROCESSORS_MODULES = []
        for frame_processor in frame_processors:
            frame_processor_module = load_processor_module(frame_processor)
            FRAME_PROCESSORS_MODULES.append(frame_processor_module)
    return FRAME_PROCESSORS_MODULES

