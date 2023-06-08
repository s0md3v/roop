import argparse
import os
from pyparsing import Any

from roop.pipeline_processing import PipelineEnvironment, Pipeline, PipelineExecutionParams, CancellationToken
from roop.pipeline_processing.extractors import BasicExtractor
from roop.pipeline_processing.collectors import BasicCollector
from roop.pipeline_processing.process_blocks import Swapper
from roop.pipeline_processing.postprocessors import BasicPostprocess

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--face', help='use this face', dest='source_img')
parser.add_argument('-t', '--target', help='replace this face', dest='target_path')
parser.add_argument('-o', '--output', help='save output to this file', dest='output_file')

args = {}
for name, value in vars(parser.parse_args()).items():
    args[name] = value


def create_pipeline():
    environment = PipelineEnvironment(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    environment.log_level = 'debug'

    pipeline = Pipeline(
        BasicExtractor(environment),
        [
            #Dummy(),
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

    if not pipeline:
        return

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