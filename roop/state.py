import os
from typing import Union

from roop.capturer import get_video_frame_total
from roop.utilities import get_temp_directory_path

PROCESSED_PREFIX = '_'


#  Checks if all frames in the target file temp folder are processed
def is_done(target_path: str) -> bool:
    return (processed_frames_count(target_path) > 0) and (0 == unprocessed_frames_count(target_path))


#  Checks if the temp directory with frames is existed and all frames are extracted (or some already processed) for target
def is_resumable(target_path: str) -> bool:
    return (processed_frames_count(target_path) > 0) or unprocessed_frames_count(target_path) == get_video_frame_total(target_path)


#  Checks if the temp directory with frames is completely processed (and can be deleted)
def is_finished(target_path: Union[None, str]) -> bool:
    return target_path is not None \
        and is_done(target_path) and processed_frames_count(target_path) == get_video_frame_total(target_path)


#  Returns count of already processed frames for this target path (0, if none). Once called, stores value in state.processed_frames_cnt global variable
def processed_frames_count(target_path: str) -> int:
    directory = get_temp_directory_path(target_path)
    if not os.path.exists(directory): return 0
    return len(
        [os.path.join(directory, file) for file in os.listdir(directory) if
         file.startswith(PROCESSED_PREFIX) and file.endswith(".png")])


#  Returns count of still unprocessed frames for this target path (0, if none).
def unprocessed_frames_count(target_path: str) -> int:
    directory = get_temp_directory_path(target_path)
    if not os.path.exists(directory): return 0
    return len([os.path.join(directory, file) for file in os.listdir(directory) if
                PROCESSED_PREFIX not in file and file.endswith(".png")])


#  Returns count all frames for this target path, processed and unprocessed (0, if none).
def total_frames_count(target_path: str) -> int:
    directory = get_temp_directory_path(target_path)
    if not os.path.exists(directory): return 0
    return len([os.path.join(directory, file) for file in os.listdir(directory) if file.endswith(".png")])


#  Returns a processed file name for an unprocessed frame file name
def get_frame_processed_name(unprocessed_frame_name: str) -> str:
    directory, filename = os.path.split(unprocessed_frame_name)
    return str(os.path.join(directory, PROCESSED_PREFIX + filename))
