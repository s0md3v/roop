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


def save_state() -> None:
    prepare_state()
    with open('.state', 'wb') as file:
        pickle.dump(state_struct, file)


def load_state(state_path: str = None) -> bool:
    if state_path is None: state_path = '.state'
    if not os.path.exists(): return False
    with open(state_path, 'rb') as file:
        roop.state.state_struct = pickle.load(file)
    return True
