import sys
import os
import shutil
import uuid

from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
import uvicorn
from typing import Annotated

import roop.globals
from roop.core import decode_execution_providers, suggest_execution_threads, limit_resources, start, \
    get_frame_processors_modules
from roop.utilities import resolve_relative_path


TEMP_FILES_PATH: str
app = FastAPI()


def update_status(message: str) -> None:
    scope: str = 'ROOP.API'
    print(f'[{scope}] {message}')


def set_init_global_params() -> None:
    global TEMP_FILES_PATH
    TEMP_FILES_PATH = resolve_relative_path('../tmp/')
    if os.path.exists(TEMP_FILES_PATH):
        shutil.rmtree(TEMP_FILES_PATH)
        update_status("Initial start. Old temp folder deleted")
    os.makedirs(TEMP_FILES_PATH)

    roop.globals.headless = True

    execution_provider = os.getenv('EXECUTION_PROVIDER')
    update_status("execution provider is set to {}".format(execution_provider))
    if execution_provider == 'CUDA':
        execution_provider_list = ['cuda']
    elif execution_provider == 'CPU':
        execution_provider_list = ['cpu']
    else:
        execution_provider_list = ['cpu']
    roop.globals.execution_providers = decode_execution_providers(execution_provider_list)

    roop.globals.temp_frame_format = os.getenv('TEMP_FRAME_FORMAT')
    roop.globals.temp_frame_quality = int(os.getenv('TEMP_FRAME_QUALITY'))
    roop.globals.output_video_quality = int(os.getenv('OUTPUT_VIDEO_QUALITY'))
    roop.globals.max_memory = int(os.getenv('MAX_MEMORY'))

    update_status("Initial roop parameters set")


def remove_request_dir(path:str) -> None:
    if os.path.exists(path):
        shutil.rmtree(path)
        update_status("Temporary request directory {} deleted".format(path))


@app.post("/start")
async def image_file(
        background_tasks: BackgroundTasks,
        src_file: Annotated[UploadFile, File()],
        target_file: Annotated[UploadFile, File()],
        frame_processor: Annotated[list, Form()] = ['face_swapper'] ,
        keep_fps: Annotated[bool, Form()] = False,
        keep_frames: Annotated[bool, Form()] = False,
        skip_audio: Annotated[bool, Form()] = False,
        many_faces: Annotated[bool, Form()] = False,
        reference_face_position: Annotated[int, Form()] = 0,
        reference_frame_number: Annotated[int, Form()] = 0,
        similar_face_distance: Annotated[float, Form()] = 0.85,
        output_video_encoder: Annotated[str, Form()] = 'libx264',
        execution_threads: Annotated[int, Form()] = suggest_execution_threads()
    ):

    roop.globals.frame_processors = frame_processor
    roop.globals.keep_fps = keep_fps
    roop.globals.keep_frames = keep_frames
    roop.globals.skip_audio = skip_audio
    roop.globals.many_faces = many_faces
    roop.globals.reference_face_position = reference_face_position
    roop.globals.reference_frame_number = reference_frame_number
    roop.globals.similar_face_distance = similar_face_distance
    roop.globals.output_video_encoder = output_video_encoder
    roop.globals.execution_threads = execution_threads

    request_uuid_str = str(uuid.uuid4())
    request_dir_path = os.path.join(TEMP_FILES_PATH, request_uuid_str)
    os.makedirs(request_dir_path)

    src_saving_path_complete = os.path.join(request_dir_path, src_file.filename)
    target_saving_path_complete = os.path.join(request_dir_path, target_file.filename)
    output_saving_path_complete = os.path.join(request_dir_path, 'output_' + target_file.filename)
    with open(src_saving_path_complete, "wb+") as file_object:
        file_object.write(src_file.file.read())
    with open(target_saving_path_complete, 'wb+') as file_obj:
        file_obj.write(target_file.file.read())

    roop.globals.source_path = src_saving_path_complete
    roop.globals.target_path = target_saving_path_complete
    roop.globals.output_path = output_saving_path_complete

    try:
        for frame_processor in get_frame_processors_modules(roop.globals.frame_processors):
            if not frame_processor.pre_check():
                sys.exit()
        limit_resources()
        start()
    except Exception as e:
        update_status('Error while running roop')
        update_status(str(e))
        raise HTTPException(status_code=500, detail="Error while running roop.")

    background_tasks.add_task(remove_request_dir, path=request_dir_path)
    return FileResponse(roop.globals.output_path)


if __name__ == "__main__":
    set_init_global_params()
    uvicorn.run(app, host="0.0.0.0", port=8000)
