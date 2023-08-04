import gradio as gr
import argparse
import os
import roop
from roop.utilities import is_image, is_video
import roop.globals
from roop import core
from shlex import quote as SQuote
import shutil
from typing import Tuple
import signal
import onnxruntime

from multiprocessing import cpu_count
import subprocess

import psutil
import string
import random
import math

from typing import List

CPU_THREADS = cpu_count()

parser = argparse.ArgumentParser()

parser.add_argument(
              "-t",
              "--theme",
    help    = "Theme for Gradio format = JohnSmith9982/small_and_pretty",
    default = "JohnSmith9982/small_and_pretty",
    type    = str
)

parser.add_argument(
              "-cc",
              "--clearcache",
    help    = "Whether to clear cache of Gradio on startup and on closing application.",
    type    = lambda x: (str(x).lower() == 'true'),
    default = True
)

args = parser.parse_args()

def encode_execution_providers(execution_providers: List[str]) -> List[str]:
    return [execution_provider.replace('ExecutionProvider', '').lower() for execution_provider in execution_providers]

def decode_execution_providers(execution_providers: List[str]) -> List[str]:
    return [provider for provider, encoded_execution_provider in zip(onnxruntime.get_available_providers(), encode_execution_providers(onnxruntime.get_available_providers()))
            if any(execution_provider in encoded_execution_provider for execution_provider in execution_providers)]

def suggest_execution_providers() -> List[str]:
    return encode_execution_providers(onnxruntime.get_available_providers())

def limit_resources() -> None:
    import platform, tensorflow
    # prevent tensorflow memory leak
    gpus = tensorflow.config.experimental.list_physical_devices('GPU')
    for gpu in gpus:
        tensorflow.config.experimental.set_virtual_device_configuration(gpu, [
            tensorflow.config.experimental.VirtualDeviceConfiguration(memory_limit=1024)
        ])
    # limit memory usage
    if roop.globals.max_memory:
        memory = roop.globals.max_memory * 1024 ** 3
        if platform.system().lower() == 'darwin':
            memory = roop.globals.max_memory * 1024 ** 6
        if platform.system().lower() == 'windows':
            import ctypes
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            kernel32.SetProcessWorkingSetSize(-1, ctypes.c_size_t(memory), ctypes.c_size_t(memory))
        else:
            import resource
            resource.setrlimit(resource.RLIMIT_DATA, (memory, memory))

def clear_gradio_temp():
    # Define the base directory
    base_dir = os.path.expanduser('~')

    # Define the rest of the Gradio directory
    gradio_dir = os.path.join(base_dir, 'AppData', 'Local', 'Temp', 'gradio')

    try:
        # Remove contents of the directory
        for filename in os.listdir(gradio_dir):
            file_path = os.path.join(gradio_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete {}. Reason: {}'.format(file_path, e))

    except FileNotFoundError:
        print("Directory not found.")
    except PermissionError:
        print("Permission Denied. Can't delete file")

if args.clearcache: signal.signal(signal.SIGINT, lambda _1, _2: clear_gradio_temp())

def generate_random_filename(length: int) -> str:
    allowed_chars = string.ascii_letters + string.digits + "_-."
    result_str = ''.join(random.choice(allowed_chars) for _ in range(length))

    return result_str

def check_nvenc_availability():
    smi_output = subprocess.check_output("nvidia-smi", shell=True).decode('utf-8')
    driver_line = [line for line in smi_output.split("\n") if "Driver Version" in line][0]

    # Find the position of 'Driver Version:' and add length of 'Driver Version:' to find start of version
    version_start = driver_line.find('Driver Version:') + len('Driver Version:')
    # Slice only Driver version part of the string
    driver_version = driver_line[version_start:].split()[0]  # get the first part before any whitespace 
    driver_version = ''.join(ch for ch in driver_version if ch.isdigit() or ch == '.')

    # NVENC became available in version 418.81
    return float(driver_version) >= 418.81

DEFAULT_CODEC = 'hevc_nvenc' if check_nvenc_availability() else 'libx265'

def start_pl(options_list: tuple, img: str, vid: str, codec: str, cpu_thread_count: int) -> Tuple[str, str]:
    '''
    Description:
        Parses options list and executes video face swapping

    Parameters:
        `options_list` (tuple): List of parameters for video conversion.
        
        `img` (str): A string that refers to an image file path.

        `vid` (str): A string that refers to a video file path.

    Returns:
        tuple: A general description of the tuple that is returned by the function.
    '''

    infos = []

    numerator = generate_random_filename(10)

    files = [
        (img, is_image, 'image'), 
        (vid, is_video, 'video')
    ]

    for file, validator, file_type in files:
        if not file:
            yield f"Don't forget to upload your {file_type}!", None
            return

        if not validator(file):
            yield f"Error has occured! {file} is not a {file_type}!", None
            return

    infos.append(f"Files are valid.")
    yield '\n'.join(infos), None

    keepfps    =  "Keep input video FPS"   in options_list
    tmp_frames =  "Keep temporary frames"  in options_list
    skip_iva   =  "Skip input video audio" in options_list
    manyfaces  =  "Many faces"             in options_list

    infos.append(f"Options assigned.")
    yield '\n'.join(infos), None

    con_dict   = {
                  "Keep input video FPS"   :  keepfps,
                  "Keep temporary frames"  :  tmp_frames,
                  "Skip input video audio" :  skip_iva,
                  "Many faces"             :  manyfaces
                }
    
    for inf, con in con_dict.items():
        infos.append(f"[{inf}: {con}];")
        yield "\n".join(infos), None
    
    infos.append(f"CPU threads given: {cpu_thread_count}")
    yield '\n'.join(infos), None

    roop.globals.source_path = img
    roop.globals.target_path = vid
    roop.globals.keep_fps = keepfps
    roop.globals.keep_frames = tmp_frames
    roop.globals.many_faces = manyfaces
    roop.globals.skip_audio = skip_iva
    roop.globals.temp_frame_quality = 0
    roop.globals.output_video_quality = 0
    roop.globals.temp_frame_format = img.split('.')[-1].lower()
    roop.globals.execution_providers = decode_execution_providers(suggest_execution_providers())
    roop.globals.reference_frame_number = 0
    roop.globals.reference_face_position = 0
    roop.globals.similar_face_distance = 0.85
    roop.globals.max_memory = (psutil.virtual_memory().total / (1024 ** 3)) / 4

    roop.globals.output_video_encoder = codec
    roop.globals.execution_threads = cpu_thread_count

    ofilename = "{}{}.{}".format(
        (vid.split("\\")[-1].split(".")[0]),
        numerator,
        (vid.split("\\")[-1].split(".")[-1])
    )

    roop.globals.output_path = os.path.join(os.path.dirname(vid), ofilename)
    
    roop.globals.frame_processors = ['face_swapper']

    infos.append(f"Values assigned.")
    yield  '\n'.join(infos), None

    for info in core.startGradio(infos):
        yield info, None

    yield  '\n'.join(infos), roop.globals.output_path
    return '\n'.join(infos), roop.globals.output_path

def GradioInit(UTheme="JohnSmith9982/small_and_pretty"):
    with gr.Blocks(theme = UTheme, title = "Roop-Web") as app:
        gr.HTML("<h1>Roop-WebUI-Fork By Alex</h1>")
        gr.Markdown("sex")
        with gr.Tabs():
            with gr.TabItem(label = "Roop"):
                with gr.Group():
                    with gr.Row():
                        inpimg = gr.Image(
                            interactive = True,
                            label = "Upload an image to get the face from",
                            type="filepath",
                            scale=1,
                        )

                        inpvid = gr.Video(
                            interactive = True,
                            label = "Upload a video to be processed",
                        )

                        with gr.Column():
                            options = gr.CheckboxGroup(
                                label = "Options for Conversion",
                                choices = [
                                    "Keep input video FPS",
                                    "Keep temporary frames",
                                    "Skip input video audio",
                                    "Many faces",
                                ],
                            )

                            codec = gr.Radio(
                                value = DEFAULT_CODEC,
                                label = "Video codec",
                                type  = 'value',
                                info  = "Output video codec. "
                                        "Keep in mind that libx264 doesn't display correctly in Gradio's UI.",
                                choices = [
                                    "libx264",
                                    "libx265",
                                    "libvpx-vp9",
                                    "h264_nvenc",
                                    "hevc_nvenc"
                                ]
                            )
                    
                with gr.Row():
                    _1 = gr.Radio(
                        value = '',
                        show_label= False,
                        container = False,
                        interactive = False,
                    )
                    _2 = gr.Radio(
                        value = '',
                        show_label= False,
                        container = False,
                        interactive = False,
                    )

                    cpucount = gr.Slider(
                        label = "Amount of CPU threads to use",
                        step = 1,
                        minimum = 1,
                        value = math.floor(CPU_THREADS / 3),
                        maximum = CPU_THREADS,
                        interactive = True,
                        container = False,
                    )
                with gr.Row():
                    startbtn = gr.Button(
                    value = "Start",
                    variant = 'primary',
                    )

                    clearbtn = gr.ClearButton(
                        value = "Clear",
                        variant = 'primary',
                    )

                    prevwbtn = gr.Button(
                        value = "Preview",
                        variant = 'primary',
                    )
                    
                with gr.Row():
                    outputvid = gr.Video (
                        interactive = False,
                        label = "Processed video with applied face.",
                    )

                    info0 = gr.Textbox (
                        interactive = False,
                        lines = 8,
                        label = "Log",
                    )

                    clearbtn.add (
                        components = [
                            inpvid,
                            outputvid,
                            inpimg,
                            info0,
                        ]
                    )

                    clearbtn.click(
                        fn=clear_gradio_temp
                    )

                    startbtn.click(
                        fn=start_pl,
                        inputs = [
                            options,
                            inpimg,
                            inpvid,
                            codec,
                            cpucount
                        ],
                        outputs = [
                            info0,
                            outputvid
                        ]
                    )

                    prevwbtn.click(
                        fn = lambda: "Preview hasn't been implemented yet :(",
                        inputs = [],
                        outputs = [info0]
                    )

        app.queue(concurrency_count=511, max_size=1022).launch(
                server_name="0.0.0.0",
                inbrowser=True,
                server_port=7865,
                quiet=False,
            )

def preinit():
    if not core.pre_check_nonctk():
        return
    for frame_processor in core.get_frame_processors_modules(roop.globals.frame_processors):
        if not frame_processor.pre_check():
            return
    limit_resources()

if __name__ == "__main__":
    preinit()
    clear_gradio_temp()
    GradioInit(UTheme=SQuote(args.theme))