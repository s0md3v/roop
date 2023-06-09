import os
import tkinter as tk
from tkinter import filedialog, LEFT
from typing import Callable, Any, Tuple

import cv2
from PIL import Image, ImageTk, ImageOps
import numpy as np

import roop.globals
from roop.analyser import get_one_face, get_many_faces, get_face_comparator, get_feat
from roop.capturer import get_video_frame
from roop.swapper import process_faces
from roop.utilities import is_image, is_video

PRIMARY_COLOR = '#2d3436'
SECONDARY_COLOR = '#74b9ff'
TERTIARY_COLOR = '#f1c40f'
ACCENT_COLOR = '#2ecc71'
WINDOW_HEIGHT = 700
WINDOW_WIDTH = 600
PREVIEW_MAX_HEIGHT = 700
PREVIEW_MAX_WIDTH = 1200
RECENT_DIRECTORY_SOURCE = None
RECENT_DIRECTORY_TARGET = None
RECENT_DIRECTORY_OUTPUT = None


def init(start: Callable, destroy: Callable) -> tk.Tk:
    global ROOT, PREVIEW, SELECTIVE_FACE_PREVIEW, crop_faces

    ROOT = create_root(start, destroy)
    PREVIEW = create_preview(ROOT)
    SELECTIVE_FACE_PREVIEW = create_selective_faces(ROOT)
    crop_faces = []

    return ROOT


def create_root(start: Callable, destroy: Callable) -> tk.Tk:
    global source_label, target_label, status_label

    root = tk.Tk()
    root.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
    root.title('roop')
    root.configure(bg=PRIMARY_COLOR)
    root.option_add('*Font', ('Arial', 11))
    root.protocol('WM_DELETE_WINDOW', lambda: destroy())

    source_label = tk.Label(root, bg=PRIMARY_COLOR)
    source_label.place(relx=0.1, rely=0.1, relwidth=0.3, relheight=0.25)

    target_label = tk.Label(root, bg=PRIMARY_COLOR)
    target_label.place(relx=0.6, rely=0.1, relwidth=0.3, relheight=0.25)

    source_button = create_primary_button(root, 'Select a face', lambda: select_source_path())
    source_button.place(relx=0.1, rely=0.4, relwidth=0.3, relheight=0.1)

    target_button = create_primary_button(root, 'Select a target', lambda: select_target_path())
    target_button.place(relx=0.6, rely=0.4, relwidth=0.3, relheight=0.1)

    keep_fps_value = tk.BooleanVar(value=roop.globals.keep_fps)
    keep_fps_checkbox = create_checkbox(root, 'Limit to 30 fps', keep_fps_value, lambda: setattr(roop.globals, 'keep_fps', not roop.globals.keep_fps))
    keep_fps_checkbox.place(relx=0.1, rely=0.6)

    keep_frames_value = tk.BooleanVar(value=roop.globals.keep_frames)
    keep_frames_checkbox = create_checkbox(root, 'Keep frames dir', keep_frames_value, lambda: setattr(roop.globals, 'keep_frames', keep_frames_value.get()))
    keep_frames_checkbox.place(relx=0.1, rely=0.65)

    keep_audio_value = tk.BooleanVar(value=roop.globals.keep_audio)
    keep_audio_checkbox = create_checkbox(root, 'Keep original audio', keep_audio_value, lambda: setattr(roop.globals, 'keep_audio', keep_audio_value.get()))
    keep_audio_checkbox.place(relx=0.6, rely=0.6)

    many_faces_value = tk.BooleanVar(value=roop.globals.many_faces)
    many_faces_checkbox = create_checkbox(root, 'Replace all faces', many_faces_value, lambda: setattr(roop.globals, 'many_faces', many_faces_value.get()))
    many_faces_checkbox.place(relx=0.6, rely=0.65)

    start_button = create_secondary_button(root, 'Start', lambda: select_output_path(start))
    start_button.place(relx=0.15, rely=0.75, relwidth=0.2, relheight=0.05)

    stop_button = create_secondary_button(root, 'Destroy', lambda: destroy())
    stop_button.place(relx=0.4, rely=0.75, relwidth=0.2, relheight=0.05)

    preview_button = create_secondary_button(root, 'Preview', lambda: toggle_preview())
    preview_button.place(relx=0.65, rely=0.75, relwidth=0.2, relheight=0.05)

    status_label = tk.Label(root, justify='center', text='Status: None', fg=ACCENT_COLOR, bg=PRIMARY_COLOR)
    status_label.place(relx=0.1, rely=0.9)

    return root


def create_preview(parent) -> tk.Toplevel:
    global preview_label, preview_scale, selective_face_value, selective_face_checkbox

    preview = tk.Toplevel(parent)
    preview.withdraw()
    preview.title('Preview')
    preview.configure(bg=PRIMARY_COLOR)
    preview.option_add('*Font', ('Arial', 11))
    preview.protocol('WM_DELETE_WINDOW', lambda: toggle_preview())
    preview.resizable(width=False, height=False)

    preview_label = tk.Label(preview, bg=PRIMARY_COLOR)
    preview_label.pack(fill='both', expand=True)

    preview_scale = tk.Scale(preview, orient='horizontal', command=lambda frame_value: update_preview(int(frame_value)))
    preview_scale.pack(fill='x')

    selective_face_value = tk.BooleanVar(value=roop.globals.selective_face_checkbox)
    selective_face_value.trace('w', toggle_selective_preview)
    selective_face_checkbox = create_checkbox_in_preview(preview, 'Selective face', selective_face_value,
                                              lambda: setattr(roop.globals, 'selective_face_checkbox',
                                                              selective_face_value.get()))
    selective_face_checkbox.pack(fill='x', side=LEFT)

    return preview


def create_selective_faces(parent) -> tk.Toplevel:
    preview = tk.Toplevel(parent)
    preview.withdraw()
    preview.title('Select face')
    preview.configure(bg=PRIMARY_COLOR)
    preview.option_add('*Font', ('Arial', 11))
    preview.protocol('WM_DELETE_WINDOW', lambda: selective_face_value.set(False))
    preview.resizable(width=False, height=False)

    preview_label = tk.Label(preview, bg=PRIMARY_COLOR)
    preview_label.pack(fill='both', expand=True)

    return preview


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
        borderwidth=4,
        highlightthickness=0
    )


def create_checkbox_in_preview(parent: Any, text: str, variable: tk.BooleanVar, command: Callable) -> tk.Checkbutton:
    return tk.Checkbutton(
        parent,
        text=text,
        variable=variable,
        command=command,
        bg=PRIMARY_COLOR,
        fg=SECONDARY_COLOR,
        relief='flat',
        highlightthickness=4,
        highlightbackground=SECONDARY_COLOR,
        activebackground=SECONDARY_COLOR,
        borderwidth=4,
        selectcolor=PRIMARY_COLOR
    )


def update_status(text: str) -> None:
    status_label['text'] = text
    ROOT.update()


def select_source_path():
    global RECENT_DIRECTORY_SOURCE
    source_path = filedialog.askopenfilename(title='Select an face image', initialdir=RECENT_DIRECTORY_SOURCE)
    if is_image(source_path):
        roop.globals.source_path = source_path
        RECENT_DIRECTORY_SOURCE = os.path.dirname(roop.globals.source_path)
        image = render_image_preview(roop.globals.source_path, (200, 200))
        source_label.configure(image=image)
        source_label.image = image
    else:
        roop.globals.source_path = None
        source_label.configure(image=None)
        source_label.image = None


def select_target_path():
    global RECENT_DIRECTORY_TARGET
    target_path = filedialog.askopenfilename(title='Select an image or video target', initialdir=RECENT_DIRECTORY_TARGET)
    if is_image(target_path):
        roop.globals.target_path = target_path
        RECENT_DIRECTORY_TARGET = os.path.dirname(roop.globals.target_path)
        image = render_image_preview(roop.globals.target_path)
        target_label.configure(image=image)
        target_label.image = image
    elif is_video(target_path):
        roop.globals.target_path = target_path
        RECENT_DIRECTORY_TARGET = os.path.dirname(roop.globals.target_path)
        video_frame = render_video_preview(target_path, (200, 200))
        target_label.configure(image=video_frame)
        target_label.image = video_frame
    else:
        roop.globals.target_path = None
        target_label.configure(image=None)
        target_label.image = None


def select_output_path(start):
    global RECENT_DIRECTORY_OUTPUT
    if is_image(roop.globals.target_path):
        output_path = filedialog.asksaveasfilename(title='Save image output', initialfile='output.png', initialdir=RECENT_DIRECTORY_OUTPUT)
    elif is_video(roop.globals.target_path):
        output_path = filedialog.asksaveasfilename(title='Save video output', initialfile='output.mp4', initialdir=RECENT_DIRECTORY_OUTPUT)
    if output_path:
        roop.globals.output_path = output_path
        RECENT_DIRECTORY_OUTPUT = os.path.dirname(roop.globals.output_path)
        start()


def render_image_preview(image_path: str, dimensions: Tuple[int, int] = None) -> ImageTk.PhotoImage:
    image = Image.open(image_path)
    if dimensions:
        image = ImageOps.fit(image, dimensions, Image.LANCZOS)
    return ImageTk.PhotoImage(image)


def render_video_preview(video_path: str, dimensions: Tuple[int, int] = None, frame_number: int = 1) -> ImageTk.PhotoImage:
    capture = cv2.VideoCapture(video_path)
    if frame_number:
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    has_frame, frame = capture.read()
    if has_frame:
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if dimensions:
            image = ImageOps.fit(image, dimensions, Image.LANCZOS)
        return ImageTk.PhotoImage(image)
    capture.release()
    cv2.destroyAllWindows()


def toggle_preview() -> None:
    if PREVIEW.state() == 'normal':
        PREVIEW.withdraw()
    else:
        if roop.globals.many_faces or not roop.globals.target_path:
            selective_face_checkbox.config(state='disabled')
        else:
            selective_face_checkbox.config(state='normal')
        update_preview(1)
        PREVIEW.deiconify()


def toggle_selective_preview(*args, **kwargs) -> None:
    if kwargs.get('selected'):
        SELECTIVE_FACE_PREVIEW.withdraw()
        return
    if selective_face_value.get():
        SELECTIVE_FACE_PREVIEW.deiconify()
        update_preview(int(preview_scale.get()))
    else:
        SELECTIVE_FACE_PREVIEW.withdraw()


def update_selective_faces(faces, frame_number: int):
    global crop_faces

    while len(crop_faces) > 0:
        b = crop_faces.pop()
        b["button"].destroy()
        b["button"].update()
    for i in range(len(faces)):
        bbox = faces[i].bbox.astype(np.int)
        img = get_video_frame(roop.globals.target_path, frame_number)[bbox[1]:bbox[3], bbox[0]:bbox[2]]

        pil_img = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))
        crop_faces.append(
            {
                "face": faces[i],
                "img": img,
                "button": tk.Button(SELECTIVE_FACE_PREVIEW, text=f'{i}', image=pil_img, command=lambda i=i: select_face_handler(crop_faces[i]['img']))
            }
        )

        crop_faces[i]["button"].pack()
        crop_faces[i]["button"].image = pil_img


def select_face_handler(image_data):
    toggle_selective_preview(selected=True)
    roop.globals.selective_face = image_data

    update_preview(int(preview_scale.get()) if int(preview_scale.get()) > 0 else 1)


def update_preview(frame_number: int) -> None:

    if selective_face_value.get():
        update_selective_faces(get_many_faces(get_video_frame(roop.globals.target_path, frame_number)), frame_number)
    if roop.globals.source_path and roop.globals.target_path and frame_number:
        video_frame = process_faces(
            get_one_face(cv2.imread(roop.globals.source_path)),
            get_video_frame(roop.globals.target_path, frame_number)
        )
        image = Image.fromarray(video_frame)
        image = ImageOps.contain(image, (PREVIEW_MAX_WIDTH, PREVIEW_MAX_HEIGHT), Image.LANCZOS)
        image = ImageTk.PhotoImage(image)
        preview_label.configure(image=image)
        preview_label.image = image
