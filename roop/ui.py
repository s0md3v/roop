import os
import tkinter as tk
from tkinter import filedialog
from typing import Callable, Any

import cv2
from PIL import Image, ImageTk, ImageOps
import roop.globals
from roop.utilities import is_image, is_video

PRIMARY_COLOR = '#2d3436'
SECONDARY_COLOR = '#74b9ff'
TERTIARY_COLOR = '#f1c40f'
ACCENT_COLOR = '#2ecc71'
WINDOW_HEIGHT = 700
WINDOW_WIDTH = 600
MAX_PREVIEW_SIZE = 800


def init(start: Callable, destroy: Callable):
    global WINDOW, source_label, target_label, status_label

    WINDOW = tk.Tk()
    WINDOW.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
    WINDOW.title('roop')
    WINDOW.configure(bg=PRIMARY_COLOR)
    WINDOW.option_add('*Font', ('Arial', 11))

    source_label = tk.Label(bg=PRIMARY_COLOR)
    source_label.place(relx=0.1, rely=0.1, relwidth=0.3, relheight=0.25)

    target_label = tk.Label(bg=PRIMARY_COLOR)
    target_label.place(relx=0.6, rely=0.1, relwidth=0.3, relheight=0.25)

    source_button = create_primary_button(WINDOW, 'Select a face', lambda: select_source_path())
    source_button.place(relx=0.1, rely=0.4, relwidth=0.3, relheight=0.1)

    target_button = create_primary_button(WINDOW, 'Select a target', lambda: select_target_path())
    target_button.place(relx=0.6, rely=0.4, relwidth=0.3, relheight=0.1)

    keep_fps_value = tk.BooleanVar(value=roop.globals.keep_fps)
    keep_fps_checkbox = create_checkbox(WINDOW, 'Limit to 30 fps', keep_fps_value, lambda: setattr(roop.globals, 'keep_fps', not roop.globals.keep_fps))
    keep_fps_checkbox.place(relx=0.1, rely=0.6)

    keep_frames_value = tk.BooleanVar(value=roop.globals.keep_frames)
    keep_frames_checkbox = create_checkbox(WINDOW, 'Keep frames dir', keep_frames_value, lambda: setattr(roop.globals, 'keep_frames', keep_frames_value.get()))
    keep_frames_checkbox.place(relx=0.1, rely=0.65)

    keep_audio_value = tk.BooleanVar(value=roop.globals.keep_audio)
    keep_audio_checkbox = create_checkbox(WINDOW, 'Keep original audio', keep_frames_value, lambda: setattr(roop.globals, 'keep_audio', keep_audio_value.get()))
    keep_audio_checkbox.place(relx=0.6, rely=0.6)

    many_faces_value = tk.BooleanVar(value=roop.globals.many_faces)
    many_faces_checkbox = create_checkbox(WINDOW, 'Replace all faces', many_faces_value, lambda: setattr(roop.globals, 'many_faces', keep_audio_value.get()))
    many_faces_checkbox.place(relx=0.6, rely=0.65)

    start_button = create_secondary_button(WINDOW, 'Start', lambda: select_output_path(start))
    start_button.place(relx=0.15, rely=0.75, relwidth=0.2, relheight=0.05)

    stop_button = create_secondary_button(WINDOW, 'Destroy', lambda: destroy())
    stop_button.place(relx=0.4, rely=0.75, relwidth=0.2, relheight=0.05)

    preview_button = create_secondary_button(WINDOW, 'Preview', lambda: None)
    preview_button.place(relx=0.65, rely=0.75, relwidth=0.2, relheight=0.05)
    preview_button.config(state='disabled')

    status_label = tk.Label(WINDOW, justify='center', text='Status: UI under heavy development, more features will soon be (re)added', fg=ACCENT_COLOR, bg=PRIMARY_COLOR)
    status_label.place(relx=0.1, rely=0.9)

    return WINDOW


def create_primary_button(parent: Any, text: str, command: Callable) -> tk.Button:
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=PRIMARY_COLOR,
        fg=SECONDARY_COLOR,
        relief='flat',
        highlightthickness=4,
        highlightbackground=SECONDARY_COLOR,
        activebackground=SECONDARY_COLOR,
        borderwidth=4
    )


def create_secondary_button(parent: Any, text: str, command: Callable) -> tk.Button:
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=TERTIARY_COLOR,
        relief='flat',
        borderwidth=0,
        highlightthickness=0
    )


def create_checkbox(parent: Any, text: str, variable: tk.BooleanVar, command: Callable) -> tk.Checkbutton:
    return tk.Checkbutton(
        parent,
        text=text,
        variable=variable,
        command=command,
        relief='flat',
        bg=PRIMARY_COLOR,
        activebackground=PRIMARY_COLOR,
        activeforeground=SECONDARY_COLOR,
        selectcolor=PRIMARY_COLOR,
        fg=SECONDARY_COLOR,
        borderwidth=0,
        highlightthickness=0
    )


def update_status(text: str) -> None:
    status_label['text'] = text
    WINDOW.update()


def select_source_path():
    source_path = filedialog.askopenfilename(title='Select an face image')
    if is_image(source_path):
        roop.globals.source_path = source_path
        image = render_image_preview(roop.globals.source_path)
        source_label.configure(image=image)
        source_label.image = image
    else:
        roop.globals.source_path = None
        source_label.configure(image=None)
        source_label.image = None


def select_target_path():
    target_path = filedialog.askopenfilename(title='Select an image or video target')
    if is_image(target_path):
        roop.globals.target_path = target_path
        image = render_image_preview(roop.globals.target_path)
        target_label.configure(image=image)
        target_label.image = image
    elif is_video(target_path):
        roop.globals.target_path = target_path
        video_frame = render_video_preview(target_path)
        target_label.configure(image=video_frame)
        target_label.image = video_frame
    else:
        roop.globals.target_path = None
        target_label.configure(image=None)
        target_label.image = None


def select_output_path(start):
    output_path = filedialog.askopenfilename(title='Save to output file')
    if os.path.isfile(output_path):
        roop.globals.output_path = output_path
        start()


def render_image_preview(image_path: str) -> ImageTk.PhotoImage:
    image = Image.open(image_path)
    image = ImageOps.fit(image, (200, 200), Image.LANCZOS)
    return ImageTk.PhotoImage(image)


def render_video_preview(target_path: str) -> ImageTk.PhotoImage:
    capture = cv2.VideoCapture(target_path)
    total_frames = capture.get(cv2.CAP_PROP_FRAME_COUNT)
    capture.set(cv2.CAP_PROP_POS_FRAMES, total_frames / 2)
    has_frame, frame = capture.read()
    if has_frame:
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        image = ImageOps.fit(image, (200, 200), Image.LANCZOS)
        return ImageTk.PhotoImage(image)
    capture.release()
    cv2.destroyAllWindows()

