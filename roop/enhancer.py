import cv2
import torch
import threading
from tqdm import tqdm
from torchvision.transforms.functional import normalize
from codeformer.facelib.utils.face_restoration_helper import FaceRestoreHelper
from codeformer.basicsr.utils.registry import ARCH_REGISTRY
from codeformer.basicsr.utils import img2tensor, tensor2img

import roop.globals
from roop.utilities import conditional_download, resolve_relative_path

if 'ROCMExecutionProvider' in roop.globals.execution_providers:
    del torch

CODE_FORMER = None
THREAD_LOCK = threading.Lock()


def pre_check() -> None:
    download_directory_path = resolve_relative_path('../models')
    conditional_download(download_directory_path, ['https://github.com/sczhou/CodeFormer/releases/download/v0.1.0/codeformer.pth'])


def get_code_former():
    global CODE_FORMER
    with THREAD_LOCK:
        model_path = resolve_relative_path('../models/codeformer.pth')
        if CODE_FORMER is None:
            model = torch.load(model_path)['params_ema']
            CODE_FORMER = ARCH_REGISTRY.get('CodeFormer')(
                dim_embd=512,
                codebook_size=1024,
                n_head=8,
                n_layers=9,
                connect_list=['32', '64', '128', '256'],
            ).to('cuda')
            CODE_FORMER.load_state_dict(model)
            CODE_FORMER.eval()
        return CODE_FORMER
    

def get_face_enhancer(FACE_ENHANCER):
    if FACE_ENHANCER is None:
        FACE_ENHANCER = FaceRestoreHelper(
        upscale_factor = int(2),
        face_size=512,
        crop_ratio=(1, 1),
        det_model='retinaface_resnet50',
        save_ext='png',
        use_parse=True,
        device='cuda',
    )
    return FACE_ENHANCER


def enhance_face_in_frame(cropped_faces):
    try:
        for _, cropped_face in enumerate(cropped_faces):
            face_in_tensor = normalize_face(cropped_face)
            faces_enhanced = restore_face(face_in_tensor)
            return faces_enhanced
    except RuntimeError as error:
        print(f'Failed inference for CodeFormer-code: {error}')


def process_faces(source_face: any, frame: any) -> any:
    try:
        face_helper = get_face_enhancer(None)
        face_helper.read_image(frame)
        # get face landmarks for each face
        face_helper.get_face_landmarks_5(
            only_center_face=False, resize=640, eye_dist_threshold=5
        )
        # align and warp each face
        face_helper.align_warp_face()
        cropped_faces = face_helper.cropped_faces
        face_enhanced = enhance_face_in_frame(cropped_faces)
        face_helper.add_restored_face(face_enhanced)
        face_helper.get_inverse_affine()
        result = face_helper.paste_faces_to_input_image()
        face_helper.clean_all()
        return result
    except RuntimeError as error:
        print(f'Failed inference for CodeFormer-code-paste: {error}')


def normalize_face(face):
    face_in_tensor = img2tensor(face / 255.0, bgr2rgb=True, float32=True)
    normalize(face_in_tensor, (0.5, 0.5, 0.5), (0.5, 0.5, 0.5), inplace=True)
    return face_in_tensor.unsqueeze(0).to('cuda')


def enhance_face_in_tensor(face_in_tensor, codeformer_fidelity = 0.6):
    with torch.no_grad():
        enhanced_face_in_tensor = get_code_former()(face_in_tensor, w=codeformer_fidelity, adain=True)[0]
    return enhanced_face_in_tensor


def convert_tensor_to_image(enhanced_face_in_tensor):
    restored_face = tensor2img(enhanced_face_in_tensor, rgb2bgr=True, min_max=(-1, 1))
    return restored_face.astype('uint8')


def restore_face(face_in_tensor):
    enhanced_face_in_tensor = enhance_face_in_tensor(face_in_tensor)
    try:
        restored_face = convert_tensor_to_image(enhanced_face_in_tensor)
        del enhanced_face_in_tensor
    except RuntimeError as error:
        print(f'Failed inference for CodeFormer-tensor: {error}')
        restored_face = convert_tensor_to_image(face_in_tensor)
        return restored_face
    return restored_face


def process_image(source_path: str, image_path: str, output_file: str) -> None:
    source_face = None
    image = cv2.imread(image_path)
    result = process_faces(source_face, image)
    cv2.imwrite(output_file, result)


def process_frames(source_path: str, frame_paths: list[str], progress=None) -> None:
    source_face = None
    for frame_path in frame_paths:
        try:
            frame = cv2.imread(frame_path)
            result = process_faces(source_face, frame)
            cv2.imwrite(frame_path, result)
        except Exception as exception:
            print(exception)
            continue
        if progress:
            progress.update(1)


def multi_process_frame(source_img, frame_paths, progress) -> None:
    threads = []
    frames_per_thread = len(frame_paths) // roop.globals.execution_threads
    remaining_frames = len(frame_paths) % roop.globals.execution_threads
    start_index = 0
    # create threads by frames
    for _ in range(roop.globals.execution_threads):
        end_index = start_index + frames_per_thread
        if remaining_frames > 0:
            end_index += 1
            remaining_frames -= 1
        thread_frame_paths = frame_paths[start_index:end_index]
        thread = threading.Thread(target=process_frames, args=(source_img, thread_frame_paths, progress))
        threads.append(thread)
        thread.start()
        start_index = end_index
    # join threads
    for thread in threads:
        thread.join()


def process_video(source_path: str, frame_paths: list[str], mode: str) -> None:
    progress_bar_format = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
    total = len(frame_paths)
    with tqdm(total=total, desc='Processing', unit='frame', dynamic_ncols=True, bar_format=progress_bar_format) as progress:
        if mode == 'multi-processing':
            progress.set_postfix({'mode': mode, 'cores': roop.globals.cpu_cores, 'memory': roop.globals.max_memory})
            process_frames(source_path, frame_paths, progress)
        elif mode == 'multi-threading':
            progress.set_postfix({'mode': mode, 'threads': roop.globals.execution_threads, 'memory': roop.globals.max_memory})
            multi_process_frame(source_path, frame_paths, progress)
