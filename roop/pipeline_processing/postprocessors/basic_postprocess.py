import os
import shutil

from ..postprocessors import Postprocess
from ..common import run_ffmpeg


class BasicPostprocess(Postprocess):
    """Basic postprocessor"""

    def process(self, input: str, output: str) -> None:
        out_audio = output + '_audio.mp4'
        input_audio = f'{input}.aac'
        # Extract audio
        run_ffmpeg(f'-i "{input}" -vn -acodec copy "{input_audio}.aac"')
        # Merge output video and audio
        if os.path.isfile(input_audio):
            run_ffmpeg(f'-i "{output}" -i "{input}.aac" -c copy "{out_audio}"')
            os.remove(input_audio)

        if not os.path.isfile(out_audio):
            shutil.move(out_audio, output)

    def release(self) -> None:
        pass
