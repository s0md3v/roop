import os
import webbrowser
import sqlite3
import cv2
import customtkinter as ctk
from typing import Callable, Tuple
from datetime import datetime
from PIL import Image, ImageOps

import roop.globals
import roop.metadata

from roop.face_analyser import get_one_face
from roop.capturer import get_video_frame, get_video_frame_total
from roop.predicter import predict_frame
from roop.processors.frame.core import get_frame_processors_modules
from roop.utilities import is_image, is_video, resolve_relative_path

ROOT = None
ROOT_HEIGHT = 700
ROOT_WIDTH = 600

PREVIEW = None
PREVIEW_MAX_HEIGHT = 700
PREVIEW_MAX_WIDTH = 1200

RECENT_DIRECTORY_SOURCE = None
RECENT_DIRECTORY_TARGET = None
RECENT_DIRECTORY_OUTPUT = None

preview_label = None
preview_slider = None
source_label = None
target_label = None
status_label = None


def init(start: Callable[[], None], destroy: Callable[[], None]) -> ctk.CTk:
    global ROOT, PREVIEW

    ROOT = create_root(start, destroy)
    PREVIEW = create_preview(ROOT)

    return ROOT


def create_root(start: Callable[[], None], destroy: Callable[[], None]) -> ctk.CTk:
    global source_label, target_label, status_label, conn, cursor, queue_size, batch_queue_button, clear_queue_button, process_batch_button, batch_frame_queue_info

    ctk.deactivate_automatic_dpi_awareness()
    ctk.set_appearance_mode('system')
    ctk.set_default_color_theme(resolve_relative_path('ui.json'))

    root = ctk.CTk()
    root.minsize(ROOT_WIDTH, ROOT_HEIGHT)
    root.title(f'{roop.metadata.name} {roop.metadata.version}')
    root.configure()
    root.protocol('WM_DELETE_WINDOW', lambda: destroy())

    source_label = ctk.CTkLabel(root, text=None)
    source_label.place(relx=0.1, rely=0.05, relwidth=0.3, relheight=0.25)

    target_label = ctk.CTkLabel(root, text=None)
    target_label.place(relx=0.6, rely=0.05, relwidth=0.3, relheight=0.25)

    source_button = ctk.CTkButton(root, text='Select a face', cursor='hand2', command=lambda: select_source_path())
    source_button.place(relx=0.1, rely=0.32, relwidth=0.3, relheight=0.07)

    target_button = ctk.CTkButton(root, text='Select a target', cursor='hand2', command=lambda: select_target_path())
    target_button.place(relx=0.6, rely=0.32, relwidth=0.3, relheight=0.07)

    keep_fps_value = ctk.BooleanVar(value=roop.globals.keep_fps)
    keep_fps_checkbox = ctk.CTkSwitch(root, text='Keep fps', variable=keep_fps_value, cursor='hand2', command=lambda: setattr(roop.globals, 'keep_fps', not roop.globals.keep_fps))
    keep_fps_checkbox.place(relx=0.1, rely=0.45)

    keep_frames_value = ctk.BooleanVar(value=roop.globals.keep_frames)
    keep_frames_switch = ctk.CTkSwitch(root, text='Keep frames', variable=keep_frames_value, cursor='hand2', command=lambda: setattr(roop.globals, 'keep_frames', keep_frames_value.get()))
    keep_frames_switch.place(relx=0.1, rely=0.5)

    keep_audio_value = ctk.BooleanVar(value=roop.globals.keep_audio)
    keep_audio_switch = ctk.CTkSwitch(root, text='Keep audio', variable=keep_audio_value, cursor='hand2', command=lambda: setattr(roop.globals, 'keep_audio', keep_audio_value.get()))
    keep_audio_switch.place(relx=0.6, rely=0.45)

    many_faces_value = ctk.BooleanVar(value=roop.globals.many_faces)
    many_faces_switch = ctk.CTkSwitch(root, text='Many faces', variable=many_faces_value, cursor='hand2', command=lambda: setattr(roop.globals, 'many_faces', many_faces_value.get()))
    many_faces_switch.place(relx=0.6, rely=0.5)

    # -- First Line of Buttons ---------------------------------------------------------------

    start_button = ctk.CTkButton(root, text='Start', cursor='hand2', command=lambda: start_single_task(start))
    start_button.place(relx=0.15, rely=0.6, relwidth=0.2, relheight=0.05)

    stop_button = ctk.CTkButton(root, text='Destroy', cursor='hand2', command=lambda: destroy())
    stop_button.place(relx=0.4, rely=0.6, relwidth=0.2, relheight=0.05)

    preview_button = ctk.CTkButton(root, text='Preview', cursor='hand2', command=lambda: toggle_preview())
    preview_button.place(relx=0.65, rely=0.6, relwidth=0.2, relheight=0.05)

    # -- Second Line of Buttons : Batch ------------------------------------------------------

    batch_frame = ctk.CTkFrame(root)
    batch_frame.place(relx=0.1, rely=0.68, relwidth=0.8, relheight=0.2)

    batch_frame_title = ctk.CTkLabel(batch_frame, text='Batch Process')
    batch_frame_title.place(relx=0, rely=0.05, relwidth=1, relheight=0.1)

    queue_button = ctk.CTkButton(batch_frame, text='Queue Current', cursor='hand2', command=lambda: add_to_queue())
    queue_button.place(relx=0.0625, rely=0.25, relwidth=0.25, relheight=0.25)

    batch_queue_button = ctk.CTkButton(batch_frame, text='Batch Queue', cursor='hand2', state='disabled', command=lambda: batch_queue())
    batch_queue_button.place(relx=0.375, rely=0.25, relwidth=0.25, relheight=0.25)

    clear_queue_button = ctk.CTkButton(batch_frame, text='Clear Queue', cursor='hand2', state='disabled', command=lambda: clear_queue())
    clear_queue_button.place(relx=0.6875, rely=0.25, relwidth=0.25, relheight=0.25)

    process_batch_button = ctk.CTkButton(batch_frame, text='Process Batch', cursor='hand2', state='disabled', command=lambda: process_batch(start))
    process_batch_button.place(relx=0.375, rely=0.62, relwidth=0.25, relheight=0.25)

    batch_frame_queue_info = ctk.CTkLabel(batch_frame)
    batch_frame_queue_info.place(relx=0.02, rely=0.85, relheight=0.1)

    if db_exists():
        # Initializes tbe connection to the SQLite database
        db_init()

        # Creates a connection to the SQLite database file, as well as the DB itself if the file does not exist
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()  # Creates a cursor object
        update_queue_size(cursor)
        conn.commit()  # Commits the transaction
        conn.close()  # Closes the connection to the database

    else:
        queue_size=0        
        batch_frame_queue_info.configure(text='Tasks in queue: ' + str(queue_size)) # Update UI Info

    # -- Bottom Labels -----------------------------------------------------------------------

    status_label = ctk.CTkLabel(root, text=None, justify='center')
    status_label.place(relx=0.1, rely=0.9, relwidth=0.8)

    donate_label = ctk.CTkLabel(root, text='Become a GitHub Sponsor', justify='center', cursor='hand2')
    donate_label.place(relx=0.1, rely=0.95, relwidth=0.8)
    donate_label.configure(text_color=ctk.ThemeManager.theme.get('RoopDonate').get('text_color'))
    donate_label.bind('<Button>', lambda event: webbrowser.open('https://github.com/sponsors/s0md3v'))

    return root


def create_preview(parent: ctk.CTkToplevel) -> ctk.CTkToplevel:
    global preview_label, preview_slider

    preview = ctk.CTkToplevel(parent)
    preview.withdraw()
    preview.title('Preview')
    preview.configure()
    preview.protocol('WM_DELETE_WINDOW', lambda: toggle_preview())
    preview.resizable(width=False, height=False)

    preview_label = ctk.CTkLabel(preview, text=None)
    preview_label.pack(fill='both', expand=True)

    preview_slider = ctk.CTkSlider(preview, from_=0, to=0, command=lambda frame_value: update_preview(frame_value))
    return preview


def update_status(text: str) -> None:
    status_label.configure(text=text)
    ROOT.update()


def select_source_path() -> None:
    global RECENT_DIRECTORY_SOURCE

    PREVIEW.withdraw()
    source_path = ctk.filedialog.askopenfilename(title='select an source image', initialdir=RECENT_DIRECTORY_SOURCE)
    if is_image(source_path):
        roop.globals.source_path = source_path
        RECENT_DIRECTORY_SOURCE = os.path.dirname(roop.globals.source_path)
        image = render_image_preview(roop.globals.source_path, (200, 200))
        source_label.configure(image=image)

        # Enable batchButton when a source file is selected
        batch_queue_button.configure(state='normal')
    
    else:
        roop.globals.source_path = None
        source_label.configure(image=None)

        # Enable batchButton when a source file is selected
        batch_queue_button.configure(state='disabled')


def select_target_path() -> None:
    global RECENT_DIRECTORY_TARGET

    PREVIEW.withdraw()
    target_path = ctk.filedialog.askopenfilename(title='select an target image or video', initialdir=RECENT_DIRECTORY_TARGET)
    if is_image(target_path):
        roop.globals.target_path = target_path
        RECENT_DIRECTORY_TARGET = os.path.dirname(roop.globals.target_path)
        image = render_image_preview(roop.globals.target_path, (200, 200))
        target_label.configure(image=image)
    elif is_video(target_path):
        roop.globals.target_path = target_path
        RECENT_DIRECTORY_TARGET = os.path.dirname(roop.globals.target_path)
        video_frame = render_video_preview(target_path, (200, 200))
        target_label.configure(image=video_frame)
    else:
        roop.globals.target_path = None
        target_label.configure(image=None)


def start_single_task(start: Callable[[], None]) -> None:

    select_output_path()
    if roop.globals.output_path == None:
        return
    else:
        start()


def select_output_path() -> None:
    global RECENT_DIRECTORY_OUTPUT

    if is_image(roop.globals.target_path):
        output_path = ctk.filedialog.asksaveasfilename(title='save image output file', defaultextension='.png', initialfile='output.png', initialdir=RECENT_DIRECTORY_OUTPUT)
    elif is_video(roop.globals.target_path):
        output_path = ctk.filedialog.asksaveasfilename(title='save video output file', defaultextension='.mp4', initialfile='output.mp4', initialdir=RECENT_DIRECTORY_OUTPUT)
    else:
        output_path = None
    if output_path:
        roop.globals.output_path = output_path
        RECENT_DIRECTORY_OUTPUT = os.path.dirname(roop.globals.output_path)


# ------------------------------------------------------
# Section : Queue Management and Batch Process
# ------------------------------------------------------

def db_exists():
    global db_exists, db_path

    db_path = 'roop.db'
    db_exists = os.path.exists(db_path)

    # If the database does not exist return False
    if db_exists:
        return True
    else:
        return False


def db_init():
    global conn, cursor

    # Creates a connection to the SQLite database file, as well as the DB itself if the file does not exist
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()  # Creates a cursor object

    # If the database does not exist, create necessary tables
    if not db_exists:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks
            (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_path TEXT NOT NULL,
                target_path TEXT NOT NULL,
                output_path TEXT NOT NULL,
                keep_fps BOOLEAN,
                keep_frames BOOLEAN,
                keep_audio BOOLEAN,
                many_faces BOOLEAN,
                state TEXT NOT NULL DEFAULT 'Queued',
                start DATETIME,
                end DATETIME,
                duration INTEGER
            )
        ''')
        
    conn.commit()
    conn.close()  # Closes the connection to the database


def add_to_queue():

    # Copied from above
    select_output_path()
    if roop.globals.output_path == None:
        return

    # Initializes tbe connection to the SQLite database
    if not db_exists:
        db_init()

    # Creates a connection to the SQLite database file, as well as the DB itself if the file does not exist
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()  # Creates a cursor object
    
    # Inserts the current parameters into the table
    cursor.execute('''
        INSERT INTO tasks (source_path, target_path, output_path, keep_fps, keep_frames, keep_audio, many_faces, state) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (roop.globals.source_path, roop.globals.target_path, roop.globals.output_path, roop.globals.keep_fps, roop.globals.keep_frames, roop.globals.keep_audio, roop.globals.many_faces, "Queued"))

    # Update Queue size calculation and UI Info
    update_queue_size(cursor)

    conn.commit()  # Commits the transaction
    conn.close()  # Closes the connection to the database

    # Inform User
    update_status('Task added to queue')


def batch_queue():
    global RECENT_DIRECTORY_TARGET

    # Select a group of files to be transformed, all will use the same source
    fileNames = ctk.filedialog.askopenfilenames(title='select target images or videos', initialdir=RECENT_DIRECTORY_TARGET)

    # Initializes tbe connection to the SQLite database
    if not db_exists:
        db_init()

    # Creates a connection to the SQLite database file, as well as the DB itself if the file does not exist
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()  # Creates a cursor object

    # Update RECENT_DIRECTORY_TARGET based on the first file
    RECENT_DIRECTORY_TARGET = os.path.dirname(fileNames[0])

    for fileName in fileNames:
        if is_image(fileName) or is_video(fileName):

            # Generate output path
            current_date = datetime.now().strftime('%Y-%m-%d-%Hh%Mm%Ss')
            output_path = os.path.splitext(fileName)[0] + '_roop_' + current_date + os.path.splitext(fileName)[1]

            # Insert the task into the queue
            cursor.execute('''
                INSERT INTO tasks(source_path, target_path, output_path, keep_fps, keep_frames, keep_audio, many_faces, state)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (roop.globals.source_path, fileName, output_path, roop.globals.keep_fps, roop.globals.keep_frames, roop.globals.keep_audio, roop.globals.many_faces, 'Queued'))

    # Update Queue size calculation and UI Info
    update_queue_size(cursor)

    # Commit changes and close connection
    conn.commit()
    conn.close()


def clear_queue():
    # Initializes tbe connection to the SQLite database
    if not db_exists:
        db_init()

    # Creates a connection to the SQLite database file, as well as the DB itself if the file does not exist
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()  # Creates a cursor object

    # Delete tasks from the queue
    cursor.execute("DELETE FROM tasks WHERE state IN ('Queued', 'In Progress')")

    # Update Queue size calculation and UI Info
    update_queue_size(cursor)

    # Commit changes
    conn.commit()
    conn.close()


def update_queue_size(cursor):

    # Get Data from DB
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE state IN ('Queued', 'In Progress')")
    queue_size = cursor.fetchone()[0]

    if queue_size > 0:
        clear_queue_button.configure(state='normal')
        process_batch_button.configure(state='normal')

    else:
        clear_queue_button.configure(state='disabled')
        process_batch_button.configure(state='disabled')
        
    # Update UI Info
    batch_frame_queue_info.configure(text='Tasks in queue: ' + str(queue_size))
    return queue_size


def process_batch(start: Callable[[], None]):
    global RECENT_DIRECTORY_OUTPUT

    # establish the connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch all tasks marked 'In Queue' or 'In Progress'
    cursor.execute("SELECT * FROM tasks WHERE state IN ('Queued', 'In Progress')")
    queue_tasks = cursor.fetchall()

    # Get the number of tasks in the queue
    queue_size = len(queue_tasks)

    # Inform User
    update_status('Batch Process Running: ' + str(queue_size) + ' tasks in the queue')

    for task in queue_tasks:
        task_id, source_path, target_path, output_path, keep_fps, keep_frames, keep_audio, many_faces, _, _, _, _ = task

        # Update task status to 'In Progress' and Store start datetime
        start_time = datetime.now()
        cursor.execute("UPDATE tasks SET state = 'In Progress', start = ? WHERE task_id = ?", (start_time, task_id))
        conn.commit()  # Commit immediately after update

        # Prepare the video transformation task here
        roop.globals.source_path    = source_path
        roop.globals.target_path    = target_path
        roop.globals.output_path    = output_path
        roop.globals.keep_fps       = keep_fps
        roop.globals.keep_frames    = keep_frames
        roop.globals.keep_audio     = keep_audio
        roop.globals.many_faces     = many_faces

        RECENT_DIRECTORY_OUTPUT = os.path.dirname(roop.globals.output_path)
        
        # Processing video
        start()

        # Once task is complete, update its status to 'Completed' and calculate and store its duration, 
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        cursor.execute("UPDATE tasks SET state = 'Completed', end = ?, duration = ? WHERE task_id = ?", (end_time, duration, task_id))
        conn.commit()  # Commit immediately after update

        # Update Queue size calculation and UI Info
        update_queue_size(cursor)

    # Close the connection
    conn.close()

    # Inform User
    update_status('Batch Process Completed')

# ------------------------------------------------------

def render_image_preview(image_path: str, size: Tuple[int, int]) -> ctk.CTkImage:
    image = Image.open(image_path)
    if size:
        image = ImageOps.fit(image, size, Image.LANCZOS)
    return ctk.CTkImage(image, size=image.size)


def render_video_preview(video_path: str, size: Tuple[int, int], frame_number: int = 0) -> ctk.CTkImage:
    capture = cv2.VideoCapture(video_path)
    if frame_number:
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    has_frame, frame = capture.read()
    if has_frame:
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if size:
            image = ImageOps.fit(image, size, Image.LANCZOS)
        return ctk.CTkImage(image, size=image.size)
    capture.release()
    cv2.destroyAllWindows()


def toggle_preview() -> None:
    if PREVIEW.state() == 'normal':
        PREVIEW.withdraw()
    elif roop.globals.source_path and roop.globals.target_path:
        init_preview()
        update_preview()
        PREVIEW.deiconify()


def init_preview() -> None:
    if is_image(roop.globals.target_path):
        preview_slider.pack_forget()
    if is_video(roop.globals.target_path):
        video_frame_total = get_video_frame_total(roop.globals.target_path)
        preview_slider.configure(to=video_frame_total)
        preview_slider.pack(fill='x')
        preview_slider.set(0)


def update_preview(frame_number: int = 0) -> None:
    if roop.globals.source_path and roop.globals.target_path:
        temp_frame = get_video_frame(roop.globals.target_path, frame_number)
        if predict_frame(temp_frame):
            quit()
        for frame_processor in get_frame_processors_modules(roop.globals.frame_processors):
            temp_frame = frame_processor.process_frame(
                get_one_face(cv2.imread(roop.globals.source_path)),
                temp_frame
            )
        image = Image.fromarray(cv2.cvtColor(temp_frame, cv2.COLOR_BGR2RGB))
        image = ImageOps.contain(image, (PREVIEW_MAX_WIDTH, PREVIEW_MAX_HEIGHT), Image.LANCZOS)
        image = ctk.CTkImage(image, size=image.size)
        preview_label.configure(image=image)
