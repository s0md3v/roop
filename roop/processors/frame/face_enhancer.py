from typing import List, Any
import cv2
import torch
import threading
import numpy as np
from torchvision.transforms.functional import normalize
from codeformer.basicsr.utils.registry import ARCH_REGISTRY
from codeformer.basicsr.utils import img2tensor, tensor2img
from insightface.utils.face_align import norm_crop2

import roop.globals
import roop.processors.frame.core
from roop.face_analyser import get_many_faces
from roop.utilities import conditional_download, resolve_relative_path

if 'ROCMExecutionProvider' in roop.globals.execution_providers:
    del torch

CODE_FORMER = None
FACE_ENHANCER = None
THREAD_LOCK = threading.Lock()
THREAD_SEMAPHORE = threading.Semaphore()
NAME = 'Face Enhancer'


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


def align_warp_face(temp_frame):
    many_faces = get_many_faces(temp_frame)
    if many_faces:
        face_list = []
        matrix_list = []
        for target_face in many_faces:
            face_long_side = max(target_face.bbox[2] - target_face.bbox[0], target_face.bbox[3] - target_face.bbox[1])
            face_size = int(np.ceil(face_long_side / 128) * 128)
            face, Matrix = norm_crop2(temp_frame, target_face.kps, face_size)
            face = cv2.resize(face, (512, 512), interpolation=cv2.INTER_LINEAR)
            upscale_factor = 512 / face_size
            Matrix *= upscale_factor
            face_list.append(face)
            matrix_list.append(Matrix)
        return face_list, matrix_list
    

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


def restore_face(face_in_tensor) -> Any:
    try:
        enhanced_face_in_tensor = enhance_face_in_tensor(face_in_tensor)
        return convert_tensor_to_image(enhanced_face_in_tensor)
    except RuntimeError:
        pass
    return convert_tensor_to_image(face_in_tensor)


def enhance_face_in_frame(face_list):
    face_enhanced_list = []
    for  _, cropped_face in enumerate(face_list):
        face_in_tensor = normalize_face(cropped_face)
        face_enhanced = restore_face(face_in_tensor)
        face_enhanced_list.append(face_enhanced)
    return face_enhanced_list


def paste_face_back(temp_frame, face_enhanced_list, matrix_list):
    target_img = temp_frame
    for i, face_enhanced in enumerate(face_enhanced_list):
        matrix = matrix_list[i]
        face_enhanced_height = face_enhanced.shape[0]
        face_enhanced_width = face_enhanced.shape[1]
        inverse_matrix = cv2.invertAffineTransform(matrix)
        face_enhanced = cv2.warpAffine(face_enhanced, inverse_matrix, (target_img.shape[1], target_img.shape[0]), borderValue=0.0)
        image_white = np.full((face_enhanced_height,face_enhanced_width), 255, dtype=np.float32)
        image_white = cv2.warpAffine(image_white, inverse_matrix, (target_img.shape[1], target_img.shape[0]), borderValue=0.0)
        image_white[image_white>20] = 255
        image_mask = image_white
        mask_row_indices, mask_col_indices = np.where(image_mask==255)
        mask_height = np.max(mask_row_indices) - np.min(mask_row_indices)
        mask_width = np.max(mask_col_indices) - np.min(mask_col_indices)
        mask_size = int(np.sqrt(mask_height*mask_width))
        k_threshold = max(mask_size//10, 10)
        kernel = np.ones((k_threshold,k_threshold),np.uint8)
        image_mask = cv2.erode(image_mask,kernel,iterations = 1)
        k_threshold = max(mask_size//20, 5)
        kernel_size = (k_threshold, k_threshold)
        blur_size = tuple(2*i+1 for i in kernel_size)
        image_mask = cv2.GaussianBlur(image_mask, blur_size, 0)
        image_mask /= 255
        image_mask = np.reshape(image_mask, [image_mask.shape[0],image_mask.shape[1],1])
        image_merged = image_mask * face_enhanced + (1-image_mask) * target_img.astype(np.float32)
        image_merged = image_merged.astype(np.uint8)
        target_img = image_merged
    return target_img


def process_frame(source_face: any, temp_frame: any) -> any:
    face_list, matrix_list = align_warp_face(temp_frame)
    face_enhanced_list = enhance_face_in_frame(face_list)
    result = paste_face_back(temp_frame, face_enhanced_list, matrix_list)
    return result


def process_frames(source_path: str, frame_paths: list[str], progress=None) -> None:
    for frame_path in frame_paths:
        try:
            frame = cv2.imread(frame_path)
            result = process_frame(None, frame)
            cv2.imwrite(frame_path, result)
        except Exception as exception:
            print(exception)
            continue
        if progress:
            progress.update(1)


def process_image(source_path: str, image_path: str, output_file: str) -> None:
    image = cv2.imread(image_path)
    result = process_frame(None, image)
    cv2.imwrite(output_file, result)


def process_video(source_path: str, temp_frame_paths: List[str]) -> None:
    roop.processors.frame.core.process_video(source_path, temp_frame_paths, process_frames)
