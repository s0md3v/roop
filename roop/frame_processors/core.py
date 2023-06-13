import sys
import importlib
from typing import Any

import torch

import roop.globals

if 'ROCMExecutionProvider' in roop.globals.execution_providers:
    del torch

FRAME_PROCESSOR_MODULES = None


def get_frame_processor_modules(frame_processor: str) -> Any:
    global FRAME_PROCESSOR_MODULES

    if not FRAME_PROCESSOR_MODULES:
        try:
            FRAME_PROCESSOR_MODULES = importlib.import_module(f'roop.frame_processors.{frame_processor}')
        except ImportError:
            sys.exit()
    return FRAME_PROCESSOR_MODULES
