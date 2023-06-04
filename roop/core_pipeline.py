import argparse
import os
from pyparsing import Any

from roop.pipeline_processing.pipeline import *
from roop.pipeline_processing.extractors.basic_extractor import BasicExtractor
from roop.pipeline_processing.collectors.basic_collector import BasicCollector
from roop.pipeline_processing.blocks.dummy import Dummy
from roop.pipeline_processing.blocks.swapper import Swapper
from roop.pipeline_processing.postprocessors.basic_postprocess import BasicPostprocess

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--face', help='use this face', dest='source_img')
parser.add_argument('-t', '--target', help='replace this face', dest='target_path')
parser.add_argument('-o', '--output', help='save output to this file', dest='output_file')

args = {}
for name, value in vars(parser.parse_args()).items():
    args[name] = value

def create_pipeline():
    environment = PipelineEnvironment(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    pipeline = Pipeline(
        BasicExtractor(environment),
        [
            #Dummy()
            Swapper(environment)
        ],
        BasicCollector(environment),
        BasicPostprocess(environment)
    )
    return pipeline

def progress_handler(value: str):
    #print(value)
    return

def preview_handler(frame: Any):
    return

def run():
    pipeline = create_pipeline()

    params = PipelineExecutionParams(
        args['source_img'],
        args['target_path'],
        args['output_file'],
        progress_handler,
        preview_handler
    )
    token = CancellationToken()

    pipeline.execute(params, token)

if __name__ == '__main__':
    run()