import sys
import importlib
from concurrent.futures import ThreadPoolExecutor
from typing import Any, List
from tqdm import tqdm

import roop

FRAME_PROCESSORS_MODULES = None
FRAME_PROCESSORS_INTERFACE = [
    'pre_check',
    'pre_start',
    'process_frame',
    'process_image',
    'process_video'
]


def load_frame_processor_module(frame_processor: str) -> Any:
    try:
        frame_processor_module = importlib.import_module(f'roop.processors.frame.{frame_processor}')
        for method_name in FRAME_PROCESSORS_INTERFACE:
            if not hasattr(frame_processor_module, method_name):
                sys.exit()
    except ImportError:
        sys.exit()
    return frame_processor_module


def get_frame_processors_modules(frame_processors):
    global FRAME_PROCESSORS_MODULES
    if FRAME_PROCESSORS_MODULES is None:
        FRAME_PROCESSORS_MODULES = []
        for frame_processor in frame_processors:
            frame_processor_module = load_frame_processor_module(frame_processor)
            FRAME_PROCESSORS_MODULES.append(frame_processor_module)
    return FRAME_PROCESSORS_MODULES


def multi_process_frame(source_path: str, temp_frame_paths: List[str], process_frames, progress) -> None:
    with ThreadPoolExecutor(max_workers=roop.globals.execution_threads) as executor:
        futures = []
        for path in temp_frame_paths:
            future = executor.submit(process_frames, source_path, [path], progress)
            futures.append(future)
        for future in futures:
            future.result()


def process_video(source_path: str, frame_paths: list[str], process_frames: Any) -> None:
    progress_bar_format = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
    total = len(frame_paths)
    with tqdm(total=total, desc='Processing', unit='frame', dynamic_ncols=True, bar_format=progress_bar_format) as progress:
        progress.set_postfix({'execution_providers': roop.globals.execution_providers, 'threads': roop.globals.execution_threads, 'memory': roop.globals.max_memory})
        multi_process_frame(source_path, frame_paths, process_frames, progress)
