import tkinter as tk
from PIL import Image, ImageTk


class PreviewWindow:
    def __init__(self, master):
        self.master = master
        self.window = tk.Toplevel(self.master)
        # Override close button
        self.window.protocol("WM_DELETE_WINDOW", self.hide)
        self.window.withdraw()
        self.window.geometry("600x700")
        self.window.title("Preview")
        self.window.configure(bg="red")
        self.window.resizable(width=False, height=False)

        self.visible = False
        self.frame = tk.Frame(self.window, background="#2d3436")
        self.frame.pack_propagate(0)
        self.frame.pack(fill='both', side='left', expand='True')
        
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

    def slider_changed(self, event):
        self.frame_change(self.frame_slider.get())

    def set_test_handler(self, test_handler):
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
        img = img.resize((600, 650), Image.ANTIALIAS)
        photo_img = ImageTk.PhotoImage(img)
        img_frame = tk.Frame(self.frame)
        img_frame.place(x=0, y=0)
        img_label = tk.Label(img_frame, image=photo_img)
        img_label.image = photo_img
        img_label.pack(side='top')