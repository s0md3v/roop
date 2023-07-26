Take a video and replace the face in it with a face of your choice. You only need one image of the desired face. No dataset, no training.

You can watch some demos [here](https://drive.google.com/drive/folders/1KHv8n_rd3Lcr2v7jBq1yPSTWM554Gq8e?usp=sharing).
A Stable Diffusion extension is also available, [here](https://github.com/s0md3v/sd-webui-roop).

![demo-gif](demo.gif)

## Disclaimer

This software is meant to be a productive contribution to the rapidly growing AI-generated media industry. It will help artists with tasks such as animating a custom character or using the character as a model for clothing etc.

The developers of this software are aware of its possible unethical applications and are committed to take preventative measures against them. It has a built-in check which prevents the program from working on inappropriate media including but not limited to nudity, graphic content, sensitive material such as war footage etc. We will continue to develop this project in the positive direction while adhering to law and ethics. This project may be shut down or include watermarks on the output if requested by law.

Users of this software are expected to use this software responsibly while abiding the local law. If face of a real person is being used, users are suggested to get consent from the concerned person and clearly mention that it is a deepfake when posting content online. Developers of this software will not be responsible for actions of end-users.

### Licence/Commercial Use Disclaimer
Roop uses a lot of third party libraries as well pre-trained models. The users should keep in mind that these third party components have their own license and terms.

## How to install?

### Basic

It is more likely to work on your computer, but will be quite slow. Follow instructions for the basic installation [here](https://github.com/s0md3v/roop/wiki/1.-Installation).

### Acceleration

If you own a capable GPU and are prepared to address any software problems, you have the option to activate such acceleration, which offers significantly enhanced speed. Once you finished the basic installation, you can follow the instructions for the acceleration installation [here](https://github.com/s0md3v/roop/wiki/2.-Acceleration).

## How to use?

### UI

Executing `python run.py` command will launch this window:

![gui-demo](gui-demo.png)

Choose a face (image with desired face) and the target image/video (image/video in which you want to replace the face) and click on `Start`. Open file explorer and navigate to the directory you select your output to be in. You will find a directory named `<video_title>` where you can see the frames being swapped in realtime. Once the processing is done, it will create the output file. That's it.

## CLI

Additional command line arguments are given below. To learn out what they do, check the guide [here](https://github.com/s0md3v/roop/wiki/Advanced-Options).

```
options:
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

Using the `-s/--source`, `-t/--target` and `-o/--output` argument will run the program in headless mode.

## Credits

- [henryruhs](https://github.com/henryruhs): for being an irreplaceable contributor to the project
- [ffmpeg](https://ffmpeg.org/): for making video related operations easy
- [deepinsight](https://github.com/deepinsight): for their [insightface](https://github.com/deepinsight/insightface) project which provided a well-made library and models.
- and all developers behind libraries used in this project.
