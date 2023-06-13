import sys
from typing import List
import importlib
import multiprocessing
import torch

import roop.globals
import roop.ui as ui

if 'ROCMExecutionProvider' in roop.globals.execution_providers:
    del torch

FRAME_PROCESSOR_MODULE = None


def conditional_process_video(source_path: str, temp_frame_paths: List[str], process_video) -> None:
    pool_amount = len(temp_frame_paths) // roop.globals.cpu_cores
    if pool_amount > 2 and roop.globals.cpu_cores > 1 and roop.globals.execution_providers == ['CPUExecutionProvider']:
        POOL = multiprocessing.Pool(roop.globals.cpu_cores, maxtasksperchild=1)
        pools = []
        for i in range(0, len(temp_frame_paths), pool_amount):
            pool = POOL.apply_async(process_video, args=(source_path, temp_frame_paths[i:i + pool_amount], 'multi-processing'))
            pools.append(pool)
        for pool in pools:
            pool.get()
        POOL.close()
        POOL.join()
    else:
         process_video(roop.globals.source_path, temp_frame_paths, 'multi-threading')


def update_status(message: str) -> None:
    value = 'Status: ' + message
    print(value)
    if not roop.globals.headless:
        ui.update_status(value)


def release_resources() -> None:
    if 'CUDAExecutionProvider' in roop.globals.execution_providers:
        torch.cuda.empty_cache()


def get_frame_processor_modules(frame_processor: str):
    global FRAME_PROCESSOR_MODULE
    try:
        FRAME_PROCESSOR_MODULE = importlib.import_module(f'roop.frame_processors.{frame_processor}')
    except ImportError:
        print(f'Failed when importing module: {ImportError}')
        sys.exit()
    return FRAME_PROCESSOR_MODULE


def process_image_pipeline(source_path, target_path, output_path, frame_processors):
    for frame_processor in frame_processors:
        update_status(f'{frame_processor} in progress...')
        module = get_frame_processor_modules(frame_processor)
        module.process_image(source_path, target_path, output_path)


def process_video_pipeline(source_path, frame_paths, frame_processors):
    for frame_processor in frame_processors:
        update_status(f'{frame_processor} in progress...')
        module = get_frame_processor_modules(frame_processor)
        conditional_process_video(source_path, frame_paths, module.process_video)
        release_resources()


def module_pre_check_pipeline(frame_processors):
    for frame_processor in frame_processors:
        module = get_frame_processor_modules(frame_processor)
        module.pre_check()


