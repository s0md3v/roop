import roop.globals
import pickle

def save_state() -> None:
    with open('.state', 'wb') as file:
        pickle.dump(roop.globals, file)

def load_state(state_path: str = None) -> bool:
   if state_path is None: state_path = '.state'
   roop.globals = pickle.load(state_path)