import os
from tqdm import tqdm
import cv2
import insightface
import core.globals
from core.analyser import get_face, get_face_analyser
from threading import Thread
FACE_SWAPPER = None


def get_face_swapper():
    global FACE_SWAPPER
    if FACE_SWAPPER is None:
        model_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../inswapper_128.onnx')
        FACE_SWAPPER = insightface.model_zoo.get_model(model_path, providers=core.globals.providers)
    return FACE_SWAPPER


def process_video(source_img, frame_paths):
    source_face = get_face(cv2.imread(source_img))
    with tqdm(total=len(frame_paths), desc="Processing", unit="frame", dynamic_ncols=True, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]') as progress:
        for frame_path in frame_paths:
            frame = cv2.imread(frame_path)
            try:
                face = get_face(frame)
                if face:
                    result = get_face_swapper().get(frame, face, source_face, paste_back=True)
                    cv2.imwrite(frame_path, result)
                    progress.set_postfix(status='.', refresh=True)
                else:
                    progress.set_postfix(status='S', refresh=True)
            except Exception:
                progress.set_postfix(status='E', refresh=True)
                pass
            progress.update(1)

def face_analyser_thread(i, source_face, ):
    try:
        face = sorted(face_analyser.get(i), key=lambda x: x.bbox[0])[0]
    except:
        face = None
    yes_face = False
    if face: 
        yes_face = True
        result = swap.get(i, face, source_face, paste_back=True)
    else:
        result = i
    return yes_face, result
class ThreadWithReturnValue(Thread):
    
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args,
                                                **self._kwargs)
    def join(self, *args):
        Thread.join(self, *args)
        return self._return
    
def process_video_gpu(source_img, source_video, out, fps, gpu_threads):
    process_video_gpu_pool(source_img, source_video, out, fps, gpu_threads)

def process_video_gpu_pool(source_img, source_video, out, fps, gpu_threads):
    global face_analyser, swap
    swap = get_face_swapper()
    face_analyser = get_face_analyser()
    source_face = get_face(cv2.imread(source_img))
    cap = cv2.VideoCapture(source_video)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print('a')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_video = cv2.VideoWriter( os.path.join(out, "output.mp4"), fourcc, fps, (width, height))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    temp = []
    with tqdm(total=frame_count, desc='Processing', unit="frame", dynamic_ncols=True, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]') as progress:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            while len(temp) >= gpu_threads:
                has_face, x = temp.pop(0).join()
                output_video.write(x)
                if has_face:
                    progress.set_postfix(status='.', refresh=True)
                else:
                    progress.set_postfix(status='S', refresh=True)
                progress.update(1)
            temp.append(ThreadWithReturnValue(target=face_analyser_thread, args=(frame, source_face)))
            temp[-1].start()
def process_video_gpu_burst(source_img, source_video, out, fps, gpu_threads):
    global face_analyser, swap
    swap = get_face_swapper()
    face_analyser = get_face_analyser()
    source_face = get_face(cv2.imread(source_img))
    cap = cv2.VideoCapture(source_video)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print('a')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_video = cv2.VideoWriter( os.path.join(out, "output.mp4"), fourcc, fps, (width, height))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    temp = []
    with tqdm(total=frame_count, desc='Processing', unit="frame", dynamic_ncols=True, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]') as progress:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            temp.append(frame)
            if len(temp) >= gpu_threads:
                try:
                    threads = []
                    for i in temp:
                        threads.append(ThreadWithReturnValue(target=face_analyser_thread, args=(i, source_face)))
                    for i in threads:
                        i.start()
                    for i in threads:
                        has_face, frame = i.join()
                        output_video.write(frame)
                        if has_face:
                            progress.set_postfix(status='.', refresh=True)
                        else:
                            progress.set_postfix(status='S', refresh=True)
                        progress.update(1)
                    temp = []
                except Exception as e:
                    print(e)
                    progress.set_postfix(status='E', refresh=True)



def process_img(source_img, target_path, output_file):
    frame = cv2.imread(target_path)
    face = get_face(frame)
    source_face = get_face(cv2.imread(source_img))
    result = get_face_swapper().get(frame, face, source_face, paste_back=True)
    cv2.imwrite(output_file, result)
    print(f"\n\nImage saved as: {output_file}\n\n")
