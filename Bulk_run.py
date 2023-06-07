# Roop-Parivartanam - One Click Bulk Deepfakes by @Aditya-A-Sharma
# This is a UI with a few added functionalities for s0md3v's roop project
# GitHub Link : https://github.com/Aditya-A-Sharma/Roop-Parivartanam
# GitHum Link for roop : https://github.com/s0md3v/roop


import tkinter as tk
from tkinter import filedialog
import subprocess
import os
import time
import configparser


# Create the main window
window = tk.Tk()
window.title("Modify - One Click Bulk Faceswapper")
window.geometry("")

# Load the configuration file
config = configparser.ConfigParser()
config.read('config.ini')

# Create 'Paths' section if it doesn't exist
if 'Paths' not in config:
    config['Paths'] = {}

# Variables
activate_env_path = tk.StringVar(value=config.get('Paths', 'activate_env_path', fallback=''))
file_path = tk.StringVar(value=config.get('Paths', 'file_path', fallback=''))
face_file = tk.StringVar(value=config.get('Paths', 'face_file', fallback=''))
target_directory = tk.StringVar(value=config.get('Paths', 'target_directory', fallback=''))
GPU_mode_variable = True
GPU_mode_checkbox_var = tk.BooleanVar()
advanced_mode_variable = True
advanced_mode_checkbox_var = tk.BooleanVar()

# Function to browse and set the activation script path
def browse_activation_script():
    path = filedialog.askopenfilename(filetypes=(("Activation Script", "*.bat"), ("All Files", "*.*")))
    activate_env_path.set(path)

# Function to browse and set the Python file path
def browse_python_file():
    path = filedialog.askopenfilename(filetypes=(("Python File", "*.py"), ("All Files", "*.*")))
    file_path.set(path)

# Function to browse and set the face file path
def browse_face_file():
    path = filedialog.askopenfilename(filetypes=(("Image File", "*.jpg"), ("All Files", "*.*")))
    face_file.set(path)

# Function to browse and set the target directory
def browse_target_directory():
    path = filedialog.askdirectory()
    target_directory.set(path)

# Function to save the selected file paths to the configuration file
def save_config():
    if 'Paths' not in config:
        config['Paths'] = {}
    
    config['Paths']['activate_env_path'] = activate_env_path.get()
    config['Paths']['file_path'] = file_path.get()
    config['Paths']['face_file'] = face_file.get()
    config['Paths']['target_directory'] = target_directory.get()

    with open('config.ini', 'w') as config_file:
        config.write(config_file)

# Function to run the script
def run_script():
    
    # Save the selected file paths to the configuration file
    save_config()
    
    # Extracting file name without extension
    face_file_name = os.path.splitext(os.path.basename(face_file.get()))[0]

    def run_python_file(file_path, args):
        try:
            activate_cmd = f'{activate_env_path.get()} && '
            subprocess.run(activate_cmd + f'python {file_path} ' + ' '.join(args), check=True, shell=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running {file_path}: {e}")

    if os.path.isdir(target_directory.get()):
        for target_file_name in os.listdir(target_directory.get()):
            target_file = os.path.join(target_directory.get(), target_file_name)
            print('\n' + target_file_name)
            if os.path.isfile(target_file):
                if target_file_name.endswith('_modifyed.mp4'):
                    print(f"This file '{target_file_name}' has already been processed. Skipping...")
                    time.sleep(1)
                    continue

                output_directory = target_directory.get()  # Use the target directory as the output directory
                output_file = os.path.join(output_directory, f'{os.path.splitext(os.path.basename(target_file))[0]}_{face_file_name}_modifyed.mp4')

                if target_file_name.endswith('.mp4'):
                    processed_file_name = os.path.splitext(target_file_name)[0] + '_' +face_file_name + '_modifyed.mp4'
                    processed_file_path = os.path.join(target_directory.get(), processed_file_name)
                    print('Processed file name:', processed_file_name,'\nProcessed File Path:', processed_file_path)
                    if os.path.isfile(processed_file_path):
                        print(f"Target '{target_file_name}' already processed with '{face_file_name}' face file, output file name is '{processed_file_name}'. Not overwriting...")
                        time.sleep(1)
                        continue

                if GPU_mode_variable:
                    arguments = [
                        '--gpu',
                        '--keep-fps',
                        '--face',
                        face_file.get(),
                        '--target',
                        target_file,
                        '--output',
                        output_file
                    ]
                else:
                    arguments = [
                        '--keep-fps',
                        '--face',
                        face_file.get(),
                        '--target',
                        target_file,
                        '--output',
                        output_file
                    ]

                run_python_file(file_path.get(), arguments)
                print("Success!")
                time.sleep(1)
    else:
        target_file = target_directory.get()
        output_directory = target_directory.get()  # Use the target directory as the output directory
        output_file = os.path.join(output_directory, f'{os.path.splitext(os.path.basename(target_file))[0]}_{face_file_name}.mp4')

        if GPU_mode_variable:
            arguments = [
                '--gpu',
                '--keep-fps',
                '--face',
                face_file.get(),
                '--target',
                target_file,
                '--output',
                output_file
            ]
        else:
            arguments = [
                '--keep-fps',
                '--face',
                face_file.get(),
                '--target',
                target_file,
                '--output',
                output_file
            ]
        run_python_file(file_path.get(), arguments)
        print("Success!")
        time.sleep(1)

    print('\n********************All files processed********************')


# Function to reload the UI when the advanced mode toggle is changed
# def reload_ui():
#     # Destroy the existing UI elements
#     for widget in window.winfo_children():
#         widget.destroy()

#     # Recreate the UI elements based on the current state
#     create_ui_elements()

# Function to toggle GPU mode (Add or remove --gpu argument)
def toggle_GPU_mode():
    global GPU_mode_variable

    if GPU_mode_variable:
        GPU_mode_variable = False
        print('GPU mode deactivated')
    else:
        GPU_mode_variable = True
        print('GPU mode activated')


# Function to toggle advanced mode (show or hide the python file and its activation path)
def toggle_advanced_mode():
    global advanced_mode_variable

    if advanced_mode_variable:
        advanced_mode_variable = False
        print('Advance options now visible')
    else:
        advanced_mode_variable = True
        print('Advance options now hidden')

    create_ui_elements()

#     # Reload the UI
#     reload_ui()

# Function to create the UI elements
def create_ui_elements():
    for widget in window.winfo_children():
        widget.destroy()
    
    # Create and position the UI elements    
    # Labels
    note_label = tk.Label(window, text="Select a directory and all files within it will be processed.\nFiles will be saved in the same directory.\nNaming format will be TargetFileName_FaceFileName.mp4.\nFiles already matching a face file name will be skipped.\nUse Responsibly, do not do what you wouldn't want others to do to you.", justify='left', padx=10)
    face_file_label = tk.Label(window, text="Face File:", justify='right')
    target_directory_label = tk.Label(window, text="        Video Directory:", justify='right')
    GPU_mode_label = tk.Label(window, text="    Disable GPU Mode if cuda errors occur:", justify='right')
    advanced_mode_label = tk.Label(window, text="                 Simple Mode:", justify='right')

    # Entry
    face_file_entry = tk.Entry(window, textvariable=face_file, width=50)
    target_directory_entry = tk.Entry(window, textvariable=target_directory, width=50)
    GPU_mode_checkbox = tk.Checkbutton(window, variable=GPU_mode_checkbox_var, command=toggle_GPU_mode)
    advanced_mode_checkbox = tk.Checkbutton(window, variable=advanced_mode_checkbox_var, command=toggle_advanced_mode)

    # Button
    run_button = tk.Button(window, text="Run", command=run_script, height=2 )
    face_file_browse_button = tk.Button(window, text="Browse", command=browse_face_file)
    target_directory_browse_button = tk.Button(window, text="Browse", command=browse_target_directory)

    # Column 0
    note_label.grid(row=0, column=0, columnspan=3, pady=5, sticky="W")
    face_file_label.grid(row=1, column=0, pady=5, sticky="E")
    target_directory_label.grid(row=2, column=0, pady=5, sticky="E")
    advanced_mode_label.grid(row=3, column=0, pady=5, sticky="W")

    # Column 1
    face_file_entry.grid(row=1, column=1, columnspan=3, pady=5, padx=5, sticky="NEWS")
    target_directory_entry.grid(row=2, column=1, columnspan=3, pady=5, padx=5, sticky="NEWS")
    advanced_mode_checkbox.grid(row=3, column=1, pady=5, padx=5, sticky="NEWS")

    # Column 2
    GPU_mode_label.grid(row=3, column=2, pady=5, sticky="W")

    # Column 3
    GPU_mode_checkbox.grid(row=3, column=3, pady=5, padx=5, sticky="NEWS")

    # Column 4
    run_button.grid(row=0, column=4, pady=5, padx=(0,10), sticky="NEWS")
    face_file_browse_button.grid(row=1, column=4, pady=5, padx=(0,10), sticky="NEWS")
    target_directory_browse_button.grid(row=2, column=4, pady=5, padx=(0,10), sticky="NEWS")
    
    if advanced_mode_variable:
        # Labels
        activation_script_label = tk.Label(window, text="Virtual Environment:", justify='right')
        python_file_label = tk.Label(window, text="Roop Run.py", justify='right')
        # Entry
        activation_script_entry = tk.Entry(window, textvariable=activate_env_path, width=50,)
        python_file_entry = tk.Entry(window, textvariable=file_path, width=50)
        # Button
        activation_script_browse_button = tk.Button(window, text="Browse", command=browse_activation_script)
        python_file_browse_button = tk.Button(window, text="Browse", command=browse_python_file)
        # Left_Grid
        activation_script_label.grid(row=5, column=0, pady=5, sticky="E")
        python_file_label.grid(row=6, column=0, pady=5, sticky="E")
        # Middle_Grid
        activation_script_entry.grid(row=5, column=1, columnspan=3, pady=5, padx=5, sticky="E")
        python_file_entry.grid(row=6, column=1, columnspan=3, pady=5, padx=5, sticky="E")
        # Column 4
        activation_script_browse_button.grid(row=5, column=4, pady=5, padx=(0,10), sticky="NEWS")
        python_file_browse_button.grid(row=6, column=4, pady=5, padx=(0,10), sticky="NEWS")

# Create the initial UI elements
create_ui_elements()

# Start the GUI event loop
window.mainloop()
