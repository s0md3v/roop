import roop.globals
import pickle
import os
import re
from typing import List

# Flag should be set to true when the swapping is started
swapping_in_progress: bool = False

state_struct = {
    'globals': {},
    'frames': {}
}

processed_frames = []


def prepare_state() -> None:
    """
    prepares state data (collects globals variables and processed frames numbers)
    """
    all_variables = dir(roop.globals)
    filtered_variables = {
        var: getattr(roop.globals, var) for var in all_variables
        if var not in ['onnxruntime', 'providers'] and not var.startswith('__')
    }

    roop.state.state_struct = {
        'globals': filtered_variables,
        'frames': processed_frames
    }


def save_state(state_path: str = '.state') -> bool:
    """
    :param state_path: path to the state file
    :return: if the state file saved successfully
    """
    if not swapping_in_progress:
        if os.path.exists(state_path): os.remove(state_path)
        return False
    prepare_state()
    with open(state_path, 'wb') as file:
        pickle.dump(state_struct, file)
    return True


def load_state(state_path: str = '.state') -> bool:
    """
    loads a state from a file
    :param state_path: path to the state file
    :return: if the state file is exists and loaded successfully
    """
    if not os.path.exists(state_path): return False
    with open(state_path, 'rb') as file:
        roop.state.state_struct = pickle.load(file)
        for variable_name, variable_value in roop.state.state_struct['globals'].items():
            if hasattr(roop.globals, variable_name):
                setattr(roop.globals, variable_name, variable_value)
    return True


def mark_frame_processed(frame_name: str) -> None:
    """
    marks passed frame as processed
    :param frame_name:
    """
    roop.state.processed_frames += [re.findall(r'\d+', frame_name)[0]]
    save_state()


def prepare_frames(frames_paths: List) -> List:
    """
    removes already processed frames from the list of all frames
    :param frames_paths: list of all frames to process
    :return: list of non-processed frames
    """
    frames_paths = [x for x in frames_paths if not re.findall(r'\d+', x)[0] in roop.state.state_struct['frames']]
    return frames_paths
