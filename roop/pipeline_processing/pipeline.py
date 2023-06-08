from multiprocessing import Lock, cpu_count, Process
from threading import Thread
from time import sleep
from typing import List
from tqdm import tqdm

from .pipeline_execution_params import PipelineExecutionParams
from .cancellation_token import CancellationToken
from .extractors import FramesExtractor
from .process_blocks import ProcessBlock
from .collectors import FramesCollector
from .postprocessors import Postprocess


class Pipeline:
    def __init__(
            self, 
            extractor: FramesExtractor, 
            blocks: List[ProcessBlock],
            collector: FramesCollector,
            postprocess: Postprocess
        ):
        self.extractor = extractor
        self.blocks = blocks
        self.collector = collector
        self.postprocess = postprocess

    def process_frame(self, 
            params: PipelineExecutionParams, 
            cancellation_token: CancellationToken,
            lock: Lock,
            progress: tqdm
        ):
        # Frame processing
        ret, frame = self.extractor.next()
        while ret:
            # Cancelling process
            if cancellation_token.cancelled:
                break

            # Await resume
            if cancellation_token.paused:
                sleep(1)
                continue

            for block in self.blocks:
                frame = block.process(frame)
            self.collector.collect(frame, lock)

            if params.progress_handler:
                params.progress_handler(self.extractor.current_frame)
            if params.preview_handler:
                params.preview_handler(frame)
            
            progress.update(1)
            ret, frame = self.extractor.next()

    def execute(
            self,
            params: PipelineExecutionParams, 
            cancellation_token: CancellationToken
        ):
        """Main execution method"""
        if not (params.face or params.target or params.output):
            raise ValueError('Input parameter required. Check "face", "target" or "output"')
        params.progress_handler("Init blocks")

        if self.extractor and self.collector:
            # Init blocks
            self.extractor.init(params.target)
            for block in self.blocks:
                block.init(params.face)
            size, fps, frames_count = self.extractor.info()
            self.collector.init(params.output, fps, size)

            params.progress_handler("Start processing...")
            
            progress_bar_format = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'

            with tqdm(total=frames_count, desc="Processing", unit="frame", dynamic_ncols=True, bar_format=progress_bar_format) as progress:
                # Threads
                lock = Lock()
                threads = [Thread(target = self.process_frame, args = (params, cancellation_token, lock, progress, )) for i in range(cpu_count())]
                [t.start() for t in threads]
                [t.join() for t in threads]
            
            params.progress_handler("Process finished.")
            self.extractor.release()
            self.collector.release()

        params.progress_handler("Postprocessing...")
        self.postprocess.process(params.target, params.output)
        params.progress_handler("Postprocessing finished.")

    def release(self):
        """Release resources"""
        self.extractor.release()
        for block in self.blocks:
            block.release()
        self.collector.release()