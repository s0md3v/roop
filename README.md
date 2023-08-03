# Roop


> Take a video and replace the face in it with a face of your choice. You only need one image of the desired face. No dataset, no training..

[![Build Status](https://img.shields.io/github/actions/workflow/status/s0md3v/roop/ci.yml.svg?branch=main)](https://github.com/s0md3v/roop/actions?query=workflow:ci)


## Preview

<div style="display:flex">
<img src="https://raw.githubusercontent.com/s0md3v/roop/next/.github/target-1080p.gif?sanitize=true" width="48%" />
      
<img src="https://raw.githubusercontent.com/s0md3v/roop/next/.github/output-1080p.gif?sanitize=true" width="48%" />
</div>

## Installation

Be aware, the installation needs technical skills and is not for beginners. Please do not open platform and installation related issues on GitHub. We have a very helpful [Discord](https://discord.com/invite/Y9p4ZQ2sB9) community that will guide you through your journey to install roop.

[Basic](https://roop-ai.gitbook.io/roop/installation/basic) - It is more likely to work on your computer, but will be quite slow

[Acceleration](https://roop-ai.gitbook.io/roop/installation/acceleration) - Unleash the full potential of your CPU and GPU


## Usage

Start the program with arguments:

```
python run.py [options]

-h, --help                                                                 show this help message and exit
-s SOURCE_PATH, --source SOURCE_PATH                                       select an source image
-t TARGET_PATH, --target TARGET_PATH                                       select an target image or video
-o OUTPUT_PATH, --output OUTPUT_PATH                                       select output file or directory
--frame-processor FRAME_PROCESSOR [FRAME_PROCESSOR ...]                    frame processors (choices: face_swapper, face_enhancer, ...)
--keep-fps                                                                 keep target fps
--keep-frames                                                              keep temporary frames
--skip-audio                                                               skip target audio
--many-faces                                                               process every face
--reference-face-position REFERENCE_FACE_POSITION                          position of the reference face
--reference-frame-number REFERENCE_FRAME_NUMBER                            number of the reference frame
--similar-face-distance SIMILAR_FACE_DISTANCE                              face distance used for recognition
--temp-frame-format {jpg,png}                                              image format used for frame extraction
--temp-frame-quality [0-100]                                               image quality used for frame extraction
--output-video-encoder {libx264,libx265,libvpx-vp9,h264_nvenc,hevc_nvenc}  encoder used for the output video
--output-video-quality [0-100]                                             quality used for the output video
--max-memory MAX_MEMORY                                                    maximum amount of RAM in GB
--execution-provider {cpu} [{cpu} ...]                                     available execution provider (choices: cpu, ...)
--execution-threads EXECUTION_THREADS                                      number of execution threads
-v, --version                                                              show program's version number and exit
```

### Headless

Using the `-s/--source`, `-t/--target` and `-o/--output` argument will run the program in headless mode.


## Documentation

Read the [documenation](https://roop-ai.gitbook.io/roop) for a deep dive.
