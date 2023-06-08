import os
import cv2
import glob
import numpy as np
import torch
from tqdm import tqdm


from torchvision.transforms.functional import normalize

import codeformer.app as model
from codeformer.facelib.utils.face_restoration_helper import FaceRestoreHelper
from codeformer.basicsr.utils import img2tensor, tensor2img

def face_enhancer(img:np.ndarray, codeformer_fidelity) -> np.ndarray:
    # img is Numpy array, (h, w, c), BGR, uint8, [0, 255] 
    device = model.device
    face_helper = FaceRestoreHelper(
        upscale_factor = int(2),
        face_size=512,
        crop_ratio=(1, 1),
        det_model="retinaface_resnet50",
        save_ext="png",
        use_parse=True,
        device=device,
    )
    face_helper.read_image(img)
    # get face landmarks for each face
    face_helper.get_face_landmarks_5(
        only_center_face=False, resize=640, eye_dist_threshold=5
    )
    # align and warp each face
    face_helper.align_warp_face()
    # face restoration for each cropped face
    for idx, cropped_face in enumerate(face_helper.cropped_faces):
        # prepare data
        cropped_face_t = img2tensor(cropped_face / 255.0, bgr2rgb=True, float32=True)
        normalize(cropped_face_t, (0.5, 0.5, 0.5), (0.5, 0.5, 0.5), inplace=True)
        cropped_face_t = cropped_face_t.unsqueeze(0).to(device)

        try:
            with torch.no_grad():
                output = model.codeformer_net(cropped_face_t, w=codeformer_fidelity, adain=True)[0]
                restored_face = tensor2img(output, rgb2bgr=True, min_max=(-1, 1))
            del output
            torch.cuda.empty_cache()
        except RuntimeError as error:
            print(f"Failed inference for CodeFormer: {error}")
            restored_face = tensor2img(cropped_face_t, rgb2bgr=True, min_max=(-1, 1))

        restored_face = restored_face.astype("uint8")
        face_helper.add_restored_face(restored_face)
        face_helper.get_inverse_affine()
        enhanced_face = face_helper.paste_faces_to_input_image()
    return enhanced_face

def enhance_images_in_folder(folder_path):
    image_files = glob.glob(os.path.join(folder_path, '*.jpg')) + glob.glob(os.path.join(folder_path, '*.jpeg')) + glob.glob(os.path.join(folder_path, '*.png'))
    total_images = len(image_files)
    progress_bar = tqdm(total=total_images, desc="Processing Images", leave=True)
    for image_file in image_files:
        img = cv2.imread(image_file, cv2.IMREAD_COLOR)
        enhanced_img = face_enhancer(img, codeformer_fidelity = 0.7)
        cv2.imwrite(image_file, enhanced_img)
        progress_bar.update(1)
    progress_bar.close()

    