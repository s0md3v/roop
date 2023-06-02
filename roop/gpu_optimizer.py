from roop.swapper import get_face_swapper
from roop.analyser import get_face_analyser
from threading import Thread
import cv2
from tqdm import tqdm
import os
from roop.analyser import get_face_single, get_face_many
#creates a thread and returns value when joined
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

def face_analyser_thread(i, source_face):
    #trying to find the face
    try:
        face = sorted(face_analyser.get(i), key=lambda x: x.bbox[0])[0]
    except:
        face = None
    yes_face = False
    #if face found, swapping it
    if face: 
        yes_face = True
        result = swap.get(i, face, source_face, paste_back=True)
    else:
        #if we didn't find, returning original frame
        result = i
    #returning if we got face and result frame 
    return yes_face, result

def face_analyser_thread(frame, source_face, all_faces):
    yes_face = False
    if all_faces:
        many_faces = get_face_many(frame)
        if many_faces:
            for face in many_faces:
                frame = swap.get(frame, face, source_face, paste_back=True)
            yes_face = True
    else:
        face = get_face_single(frame)
        if face:
            frame = swap.get(frame, face, source_face, paste_back=True)
            yes_face = True   
    return yes_face, frame


def process_video_gpu(source_img, source_video, out, fps, gpu_threads, all_faces):
    global face_analyser, swap
    swap = get_face_swapper()
    face_analyser = get_face_analyser()
    source_face = get_face_single(cv2.imread(source_img))
    #opening input video for read
    cap = cv2.VideoCapture(source_video)
    #opening output video for writing
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_video = cv2.VideoWriter( os.path.join(out, "output.mp4"), fourcc, fps, (width, height))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    temp = []
    with tqdm(total=frame_count, desc='Processing', unit="frame", dynamic_ncols=True, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]') as progress:
        while True:
            #getting frame
            ret, frame = cap.read()
            if not ret:
                break
            #we are having an array of length %gpu_threads%, running in parallel
            #so if array is equal or longer than gpu threads, waiting 
            while len(temp) >= gpu_threads:
                #we are order dependent, so we are forced to wait for first element to finish. When finished removing thread from the list
                has_face, x = temp.pop(0).join()
                #writing into output
                output_video.write(x)
                #updating the status
                if has_face:
                    progress.set_postfix(status='.', refresh=True)
                else:
                    progress.set_postfix(status='S', refresh=True)
                progress.update(1)
            #adding new frame to the list and starting it 
            temp.append(ThreadWithReturnValue(target=face_analyser_thread, args=(frame, source_face, all_faces)))
            temp[-1].start()