import os
import customtkinter as ctk
from typing import Callable, Tuple

import cv2
from PIL import Image, ImageTk, ImageOps

import roop.globals
from roop.analyser import get_one_face
from roop.capturer import get_video_frame
from roop.swapper import process_faces
from roop.utilities import is_image, is_video, resolve_relative_path

WINDOW_HEIGHT = 700
WINDOW_WIDTH = 600
PREVIEW_MAX_HEIGHT = 700
PREVIEW_MAX_WIDTH = 1200
RECENT_DIRECTORY_SOURCE = None
RECENT_DIRECTORY_TARGET = None
RECENT_DIRECTORY_OUTPUT = None


def init(start: Callable, destroy: Callable) -> ctk.CTk:
    global ROOT, PREVIEW

    ROOT = create_root(start, destroy)
    PREVIEW = create_preview(ROOT)

    return ROOT


def create_root(start: Callable, destroy: Callable) -> ctk.CTk:
    global source_label, target_label, status_label

    ctk.set_appearance_mode('system')
    ctk.set_default_color_theme(resolve_relative_path('ui.json'))
    root = ctk.CTk()
    root.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
    root.title('roop')
    root.configure()
    root.protocol('WM_DELETE_WINDOW', lambda: destroy())

    source_label = ctk.CTkLabel(root, text=None)
    source_label.place(relx=0.1, rely=0.1, relwidth=0.3, relheight=0.25)

    target_label = ctk.CTkLabel(root, text=None)
    target_label.place(relx=0.6, rely=0.1, relwidth=0.3, relheight=0.25)

    source_button = ctk.CTkButton(root, text='Select a face', command=lambda: select_source_path())
    source_button.place(relx=0.1, rely=0.4, relwidth=0.3, relheight=0.1)

    target_button = ctk.CTkButton(root, text='Select a target', command=lambda: select_target_path())
    target_button.place(relx=0.6, rely=0.4, relwidth=0.3, relheight=0.1)

    keep_fps_value = ctk.BooleanVar(value=roop.globals.keep_fps)
    keep_fps_checkbox = ctk.CTkSwitch(root, text='Keep fps', variable=keep_fps_value, command=lambda: setattr(roop.globals, 'keep_fps', not roop.globals.keep_fps))
    keep_fps_checkbox.place(relx=0.1, rely=0.6)

    keep_frames_value = ctk.BooleanVar(value=roop.globals.keep_frames)
    keep_frames_switch = ctk.CTkSwitch(root, text='Keep frames', variable=keep_frames_value, command=lambda: setattr(roop.globals, 'keep_frames', keep_frames_value.get()))
    keep_frames_switch.place(relx=0.1, rely=0.65)

    keep_audio_value = ctk.BooleanVar(value=roop.globals.keep_audio)
    keep_audio_switch = ctk.CTkSwitch(root, text='Keep audio', variable=keep_audio_value, command=lambda: setattr(roop.globals, 'keep_audio', keep_audio_value.get()))
    keep_audio_switch.place(relx=0.6, rely=0.6)

    many_faces_value = ctk.BooleanVar(value=roop.globals.many_faces)
    many_faces_switch = ctk.CTkSwitch(root, text='Many faces', variable=many_faces_value, command=lambda: setattr(roop.globals, 'many_faces', many_faces_value.get()))
    many_faces_switch.place(relx=0.6, rely=0.65)

    start_button = ctk.CTkButton(root, text='Start', command=lambda: select_output_path(start))
    start_button.place(relx=0.15, rely=0.75, relwidth=0.2, relheight=0.05)

    stop_button = ctk.CTkButton(root, text='Destroy', command=lambda: destroy())
    stop_button.place(relx=0.4, rely=0.75, relwidth=0.2, relheight=0.05)

    preview_button = ctk.CTkButton(root, text='Preview', command=lambda: toggle_preview())
    preview_button.place(relx=0.65, rely=0.75, relwidth=0.2, relheight=0.05)

    status_label = ctk.CTkLabel(root, text='Status: None', justify='center')
    status_label.place(relx=0.1, rely=0.9)

    return root


def create_preview(parent) -> ctk.CTkToplevel:
    global preview_label, preview_slider

    preview = ctk.CTkToplevel(parent)
    preview.withdraw()
    preview.title('Preview')
    preview.configure()
    preview.protocol('WM_DELETE_WINDOW', lambda: toggle_preview())
    preview.resizable(width=False, height=False)

    preview_label = ctk.CTkLabel(preview, text=None)
    preview_label.pack(fill='both', expand=True)

    preview_slider = ctk.CTkSlider(preview, from_=0, to=100, border_width=10, command=lambda frame_value: update_preview(frame_value))
    preview_slider.pack(fill='x')

    return preview


def update_status(text: str) -> None:
    status_label.configure(text=text)
    ROOT.update()


def select_source_path() -> None:
    global RECENT_DIRECTORY_SOURCE

    source_path = ctk.filedialog.askopenfilename(title='Select an face image', initialdir=RECENT_DIRECTORY_SOURCE)
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


def select_target_path() -> None:
    global RECENT_DIRECTORY_TARGET

    target_path = ctk.filedialog.askopenfilename(title='Select an image or video target', initialdir=RECENT_DIRECTORY_TARGET)
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
        output_path = ctk.filedialog.asksaveasfilename(title='Save image output', initialfile='output.png', initialdir=RECENT_DIRECTORY_OUTPUT)
    elif is_video(roop.globals.target_path):
        output_path = ctk.filedialog.asksaveasfilename(title='Save video output', initialfile='output.mp4', initialdir=RECENT_DIRECTORY_OUTPUT)
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
        update_preview(1)
        PREVIEW.deiconify()


def update_preview(frame_number: int) -> None:
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
