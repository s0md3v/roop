from typing import Literal
import gradio

Component = gradio.File or gradio.Image or gradio.Video
ComponentName = Literal['source_file', 'target_file']
