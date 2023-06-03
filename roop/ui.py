import tkinter as tk
from typing import Any, Callable, Tuple
from PIL import Image, ImageTk
import webbrowser
from tkinter import filedialog
from tkinter.filedialog import asksaveasfilename
import threading

from roop.utils import is_img

class PreviewWindow:

    def __init__(self, master):
        self.max_preview_size = 800

        self.master = master
        self.window = tk.Toplevel(self.master)
        # Override close button
        self.window.protocol("WM_DELETE_WINDOW", self.hide)
        self.window.withdraw()
        self.window.title("Preview")
        self.window.configure(bg="red")
        self.window.resizable(width=False, height=False)

        self.visible = False
        self.frame = tk.Frame(self.window, background="#2d3436")
        self.frame.pack(fill='both', side='left', expand='True')
        
        # Preview image
        self.img_label = tk.Label(self.frame)
        self.img_label.pack(side='top')

        # Bottom frame
        buttons_frame = tk.Frame(self.frame, background="#2d3436")
        buttons_frame.pack(fill='both', side='bottom')

        self.current_frame = tk.IntVar()
        self.frame_slider = tk.Scale(
            buttons_frame,
            from_=0, 
            to=0,
            orient='horizontal',
            variable=self.current_frame, 
            command=self.slider_changed
        )
        self.frame_slider.pack(fill='both', side='left', expand='True')

        self.test_button = tk.Button(buttons_frame, text="Test", bg="#f1c40f", relief="flat", width=15, borderwidth=0, highlightthickness=0)
        self.test_button.pack( side='right', fill='y')

    def init_slider(self, frames_count, change_handler):
        self.frame_change = change_handler
        self.frame_slider.configure(to=frames_count)
        self.frame_slider.set(0)

    def slider_changed(self, event):
        self.frame_change(self.frame_slider.get())

    def set_preview_handler(self, test_handler):
        self.test_button.config(command = test_handler)

    # Show the window
    def show(self):
        self.visible = True
        self.window.deiconify()
    
    # Hide the window
    def hide(self):
        self.visible = False
        self.window.withdraw()

    def update(self, frame):
        if not self.visible:
            return

        img = Image.fromarray(frame)
        width, height = img.size
        aspect_ratio = 1
        if width > height:
            aspect_ratio = self.max_preview_size / width
        else:
            aspect_ratio = self.max_preview_size / height
        img = img.resize(
            (
                int(width * aspect_ratio), 
                int(height * aspect_ratio)
            ), 
            Image.ANTIALIAS
        )
        photo_img = ImageTk.PhotoImage(img)
        self.img_label.configure(image=photo_img)
        self.img_label.image = photo_img


def select_face(select_face_handler: Callable[[str], None]):
    if select_face_handler:
        path = filedialog.askopenfilename(title="Select a face")
        preview_face(path)
        return select_face_handler(path)
    return None


def update_slider_handler(get_video_frame, video_path):
    return lambda frame_number: preview.update(get_video_frame(video_path, frame_number))

def test_preview(create_test_preview):
    frame = create_test_preview(preview.current_frame.get())
    preview.update(frame)

def update_slider(get_video_frame, create_test_preview, video_path, frames_amount):
    preview.init_slider(frames_amount, update_slider_handler(get_video_frame, video_path))
    preview.set_preview_handler(lambda: preview_thread(test_preview(create_test_preview)))


def analyze_target(select_target_handler: Callable[[str], Tuple[int, Any]], target_path: tk.StringVar, frames_amount: tk.IntVar):    
    path = filedialog.askopenfilename(title="Select a target")
    target_path.set(path)
    amount, frame = select_target_handler(path)
    frames_amount.set(amount)
    preview_target(frame)
    preview.update(frame)


def select_target(select_target_handler: Callable[[str], Tuple[int, Any]], target_path: tk.StringVar, frames_amount: tk.IntVar):
    if select_target_handler:
        analyze_target(select_target_handler, target_path, frames_amount)


def save_file(save_file_handler: Callable[[str], None], target_path: str):
    filename, ext = 'output.mp4', '.mp4'

    if is_img(target_path):
        filename, ext = 'output.png', '.png'

    if save_file_handler:
        return save_file_handler(asksaveasfilename(initialfile=filename, defaultextension=ext, filetypes=[("All Files","*.*"),("Videos","*.mp4")]))
    return None

def toggle_all_faces(toggle_all_faces_handler: Callable[[int], None], variable: tk.IntVar):
    if toggle_all_faces_handler:
        return lambda: toggle_all_faces_handler(variable.get())
    return None


def toggle_fps_limit(toggle_all_faces_handler: Callable[[int], None], variable: tk.IntVar):
    if toggle_all_faces_handler:
        return lambda: toggle_all_faces_handler(variable.get())
    return None


def toggle_keep_frames(toggle_keep_frames_handler: Callable[[int], None], variable: tk.IntVar):
    if toggle_keep_frames_handler:
        return lambda: toggle_keep_frames_handler(variable.get())
    return None


def create_button(parent, text, command):
    return tk.Button(
        parent, 
        text=text, 
        command=command,
        bg="#f1c40f", 
        relief="flat", 
        borderwidth=0, 
        highlightthickness=0
    )


def create_background_button(parent, text, command):
    button = create_button(parent, text, command)
    button.configure(
        bg="#2d3436", 
        fg="#74b9ff", 
        highlightthickness=4, 
        highlightbackground="#74b9ff", 
        activebackground="#74b9ff", 
        borderwidth=4
    )
    return button


def create_check(parent, text, variable, command):
    return tk.Checkbutton(
        parent, 
        anchor="w", 
        relief="groove", 
        activebackground="#2d3436", 
        activeforeground="#74b9ff", 
        selectcolor="black", 
        text=text, 
        fg="#dfe6e9", 
        borderwidth=0, 
        highlightthickness=0, 
        bg="#2d3436", 
        variable=variable, 
        command=command
    )


def preview_thread(thread_function):
    threading.Thread(target=thread_function).start()


def open_preview_window(get_video_frame, target_path):
    if (preview.visible):
        preview.hide()
    else:
        preview.show()
        if target_path:
            frame = get_video_frame(target_path)
            preview.update(frame)

def preview_face(path):
    img = Image.open(path)
    img = img.resize((180, 180), Image.ANTIALIAS)
    photo_img = ImageTk.PhotoImage(img)
    face_label.configure(image=photo_img)
    face_label.image = photo_img

def preview_target(frame):
    img = Image.fromarray(frame)
    img = img.resize((180, 180), Image.ANTIALIAS)
    photo_img = ImageTk.PhotoImage(img)
    target_label.configure(image=photo_img)
    target_label.image = photo_img

def update_status_label(value):
    status_label["text"] = value
    window.update()

def init(
    initial_values: dict,
    select_face_handler: Callable[[str], None],
    select_target_handler: Callable[[str], Tuple[int, Any]],
    toggle_all_faces_handler: Callable[[int], None],
    toggle_fps_limit_handler: Callable[[int], None],
    toggle_keep_frames_handler: Callable[[int], None],
    save_file_handler: Callable[[str], None],
    start: Callable[[], None],
    get_video_frame: Callable[[str, int], None],
    create_test_preview: Callable[[int], Any],
):
    global window, preview, face_label, target_label, status_label

    window = tk.Tk()
    window.geometry("600x700")
    window.title("roop")
    window.configure(bg="#2d3436")
    window.resizable(width=False, height=False)

    target_path = tk.StringVar()
    frames_amount = tk.IntVar()

    # Preview window
    preview = PreviewWindow(window)

    # Contact information
    support_link = tk.Label(window, text="Donate to project <3", fg="#fd79a8", bg="#2d3436", cursor="hand2", font=("Arial", 8))
    support_link.place(x=180,y=20,width=250,height=30)
    support_link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/sponsors/s0md3v"))

    left_frame = tk.Frame(window)
    left_frame.place(x=60, y=100)
    face_label = tk.Label(left_frame)
    face_label.pack(fill='both', side='top', expand=True)

    right_frame = tk.Frame(window)
    right_frame.place(x=360, y=100)
    target_label = tk.Label(right_frame)
    target_label.pack(fill='both', side='top', expand=True)

    # Select a face button
    face_button = create_background_button(window, "Select a face", lambda: [
        select_face(select_face_handler)
    ])
    face_button.place(x=60,y=320,width=180,height=80)

    # Select a target button
    target_button = create_background_button(window, "Select a target", lambda: [
        select_target(select_target_handler, target_path, frames_amount),
        update_slider(get_video_frame, create_test_preview, target_path.get(), frames_amount.get())
    ])
    target_button.place(x=360,y=320,width=180,height=80)

    # All faces checkbox
    all_faces = tk.IntVar(None, initial_values['all_faces'])
    all_faces_checkbox = create_check(window, "Process all faces in frame", all_faces, toggle_all_faces(toggle_all_faces_handler, all_faces))
    all_faces_checkbox.place(x=60,y=500,width=240,height=31)

    # FPS limit checkbox
    limit_fps = tk.IntVar(None, not initial_values['keep_fps'])
    fps_checkbox = create_check(window, "Limit FPS to 30", limit_fps, toggle_fps_limit(toggle_fps_limit_handler, limit_fps))
    fps_checkbox.place(x=60,y=475,width=240,height=31)

    # Keep frames checkbox
    keep_frames = tk.IntVar(None, initial_values['keep_frames'])
    frames_checkbox = create_check(window, "Keep frames dir", keep_frames, toggle_keep_frames(toggle_keep_frames_handler, keep_frames))
    frames_checkbox.place(x=60,y=450,width=240,height=31)

    # Start button
    start_button = create_button(window, "Start", lambda: [save_file(save_file_handler, target_path.get()), preview_thread(start)])
    start_button.place(x=170,y=560,width=120,height=49)

    # Preview button
    preview_button = create_button(window, "Preview", lambda: open_preview_window(get_video_frame, target_path.get()))
    preview_button.place(x=310,y=560,width=120,height=49)

    # Status label
    status_label = tk.Label(window, width=580, justify="center", text="Status: waiting for input...", fg="#2ecc71", bg="#2d3436")
    status_label.place(x=10,y=640,width=580,height=30)

    return window