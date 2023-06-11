import roop.globals
import json
import os
import re
from typing import List, Optional

# Flag should be set to true when the processing is started
in_progress: bool = False

state_struct = {
    'globals': {},
    'frames': []
}


def prepare_state() -> None:
    """
    prepares state data (collects globals variables and processed frames numbers)
    """
    all_variables = dir(roop.globals)
    roop.state.state_struct['globals'] = {
        var: getattr(roop.globals, var) for var in all_variables
        if var not in ['onnxruntime', 'providers', 'headless'] and not var.startswith('__')
    }


def save_state(state_path: str = '.state') -> bool:
    """
    :param state_path: path to the state file
    :return: if the state file saved successfully
    """
    if not in_progress:
        if os.path.exists(state_path): os.remove(state_path)
        return False
    prepare_state()
    with open(state_path, 'w') as file:
        json.dump(state_struct, file)
    return True


def load_state(state_path: str = '.state') -> bool:
    """
    loads a state from a file
    :param state_path: path to the state file
    :return: if the state file is exists and loaded successfully
    """
    if not os.path.exists(state_path): return False
    with open(state_path, 'r') as file:
        roop.state.state_struct = json.load(file)
        for variable_name, variable_value in roop.state.state_struct['globals'].items():
            if hasattr(roop.globals, variable_name):
                setattr(roop.globals, variable_name, variable_value)
    return True


def mark_frame_processed(frame_name: str) -> None:
    """
    marks passed frame as processed
    :param frame_name:
    """
    roop.state.state_struct['frames'].append(get_frame_number(frame_name))
    save_state()


def prepare_frames(frames_paths: List) -> List:
    """
    removes already processed frames from the list of all frames
    :param frames_paths: list of all frames to process
    :return: list of non-processed frames
    """
    frames_paths = [x for x in frames_paths if not get_frame_number(x) in roop.state.state_struct['frames']]
    return frames_paths


def exists(target_path: str) -> bool:
    """
    checks if the current state is for target_path, and frames are already extracted
    :param target_path: target path
    :return: if state is exists
    """
    return 'target_path' in roop.state.state_struct['globals'] and roop.state.state_struct['globals']['target_path'] == target_path and roop.state.state_struct['frames']

def get_frame_number(frame_name: str) -> Optional[str]:
    """
    :param frame_name:
    :return: the number part from the frame_name, or None, if frame has no number in it
    """
    matches = re.findall(r'\d+', frame_name)
    return matches[-1] if matches else None