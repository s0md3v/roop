import roop.globals
import pickle
import os
import re

state_struct = {
    'globals': {},
    'step': None,
    'frame_sets': {}
}

done_frames = []

def prepare_state():
    all_variables = dir(roop.globals)
    filtered_variables = {
        var: getattr(roop.globals, var) for var in all_variables
        if var not in ['onnxruntime', 'providers'] and not var.startswith('__')
    }

    roop.state.state_struct = {
        'globals': filtered_variables,
        'step': None,
        'frame_sets': done_frames
    }


def save_state(state_path: str = '.state') -> None:
    prepare_state()
    with open(state_path, 'wb') as file:
        pickle.dump(state_struct, file)


def load_state(state_path: str = '.state') -> bool:
    if not os.path.exists(state_path): return False
    with open(state_path, 'rb') as file:
        roop.state.state_struct = pickle.load(file)
        for variable_name, variable_value in roop.state.state_struct['globals'].items():
            if hasattr(roop.globals, variable_name):
                setattr(roop.globals, variable_name, variable_value)
    return True


def mark_frame_done(frame_name: str) -> None:
    roop.state.done_frames += [int(re.findall(r'\d+', frame_name)[0])]
    save_state()


