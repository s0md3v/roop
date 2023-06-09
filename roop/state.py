import roop.globals
import pickle
import os

state_struct = {
    'parameters': {},
    'step': None,
    'frame_sets': {}
}


def prepare_state():
    all_variables = dir(roop.globals)
    filtered_variables = {
        var: getattr(roop.globals, var) for var in all_variables
        if var not in ['onnxruntime', 'providers'] and not var.startswith('__')
    }

    roop.state.state_struct = {
        'parameters': filtered_variables,
        'step': None,
        'frame_sets': {}
    }


def save_state(state_path: str = '.state') -> None:
    prepare_state()
    with open(state_path, 'wb') as file:
        pickle.dump(state_struct, file)


def load_state(state_path: str = '.state') -> bool:
    if not os.path.exists(state_path): return False
    with open(state_path, 'rb') as file:
        roop.state.state_struct = pickle.load(file)
    return True
