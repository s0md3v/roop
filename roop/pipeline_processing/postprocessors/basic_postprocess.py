import os
import shutil

from ..postprocessors import Postprocess
from ..common import run_ffmpeg


class BasicPostprocess(Postprocess):
    """Basic postprocessor"""

    def process(self, input: str, output: str) -> None:
        out_audio = output + '_audio.mp4'
        run_ffmpeg(f'-i "{output}" -i "{input}" -c:v copy -map 0:v:0 -c:a copy -map 1:a:0 -y "{out_audio}"')
        if not os.path.isfile(out_audio):
            shutil.move(out_audio, output)

    def release(self) -> None:
        pass
