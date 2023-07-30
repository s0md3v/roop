import sys
import os
import shutil
from fastapi import FastAPI, File, UploadFile, Depends, Response
from fastapi.responses import FileResponse
import uvicorn
from pydantic import BaseModel
from typing import Optional, Literal

import roop.globals
from roop.core import decode_execution_providers, suggest_execution_threads, limit_resources, start, \
    get_frame_processors_modules, suggest_execution_providers, update_status
from roop.utilities import resolve_relative_path


app = FastAPI()

class RoopModel(BaseModel):
    frame_processor: Optional[list] = ['face_swapper']
    keep_fps: Optional[bool] = False
    keep_frames: Optional[bool] = False
    skip_audio: Optional[bool] = False
    many_faces: Optional[bool] = False
    reference_face_position: Optional[int] = 0
    reference_frame_number: Optional[int] = 0
    similar_face_distance: Optional[float] = 0.85
    temp_frame_format: Optional[Literal['png','jpg']] = 'png'
    temp_frame_quality: Optional[int] = 0
    output_video_encoder: Optional[Literal['libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc']] = 'libx264'
    output_video_quality: Optional[int] = 0
    max_memory: Optional[int] = 0
    execution_threads: Optional[int] = suggest_execution_threads()
@app.get('/get_execution_providers')
async def get_execution_provider():
    return suggest_execution_providers()


@app.post("/start_roop")
async def image_file(
        src_file: UploadFile = File(...),
        target_file: UploadFile = File(...),
        roop_parameters: RoopModel = Depends()
):
    # Removing the folder and its content if it already exists
    saving_path = resolve_relative_path('../workdir/')
    if os.path.exists(saving_path):
        shutil.rmtree(saving_path)
    os.makedirs(saving_path)

    #Get execution provider from env.
    execution_provider = os.getenv('EXECUTION_PROVIDER')
    update_status("execution provider is set to {}".format(execution_provider))
    if execution_provider == 'GPU':
        execution_provider_list = ['gpu','cpu']
    elif execution_provider == 'CPU':
        execution_provider_list = ['cpu']
    else:
        execution_provider_list = ['cpu']

    # setting paths
    src_saving_path_complete = os.path.join(saving_path, src_file.filename)
    target_saving_path_complete = os.path.join(saving_path, target_file.filename)
    output_saving_path_complete = os.path.join(saving_path, 'output_' + target_file.filename)
    with open(src_saving_path_complete, "wb+") as file_object:
        file_object.write(src_file.file.read())
    with open(target_saving_path_complete, 'wb+') as file_obj:
        file_obj.write(target_file.file.read())

    roop.globals.source_path = src_saving_path_complete
    roop.globals.target_path = target_saving_path_complete
    roop.globals.output_path = output_saving_path_complete

    # Since API starts the roop. It is always headless
    roop.globals.headless = True
    # Setting other roop parameters
    roop.globals.frame_processors = roop_parameters.frame_processor
    roop.globals.keep_fps = roop_parameters.keep_fps
    roop.globals.keep_frames = roop_parameters.keep_frames
    roop.globals.skip_audio = roop_parameters.skip_audio
    roop.globals.many_faces = roop_parameters.many_faces
    roop.globals.reference_face_position = roop_parameters.reference_face_position
    roop.globals.reference_frame_number = roop_parameters.reference_frame_number
    roop.globals.similar_face_distance = roop_parameters.similar_face_distance
    roop.globals.temp_frame_format = roop_parameters.temp_frame_format
    roop.globals.temp_frame_quality = roop_parameters.temp_frame_quality
    roop.globals.output_video_encoder = roop_parameters.output_video_encoder
    roop.globals.output_video_quality = roop_parameters.output_video_quality
    roop.globals.max_memory = roop_parameters.max_memory
    roop.globals.execution_providers = decode_execution_providers(execution_provider_list)
    roop.globals.execution_threads = roop_parameters.execution_threads

    for frame_processor in get_frame_processors_modules(roop.globals.frame_processors):
        if not frame_processor.pre_check():
            sys.exit()
    limit_resources()
    start()
    return FileResponse(roop.globals.output_path)

if __name__ == "__main__":
    if os.getenv('EXECUTION_PROVIDER') == None:
        update_status('Env variable for provider is not set. Setting default CPU.')
        os.environ['EXECUTION_PROVIDER'] = 'CPU'

    uvicorn.run(app, host="0.0.0.0", port=8000)