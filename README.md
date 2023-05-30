Take a video and replace the face in it with a face of your choice. You only need one image of the desired face. No dataset, no training.

That's it, that's the software. You can watch some demos [here](https://drive.google.com/drive/folders/1KHv8n_rd3Lcr2v7jBq1yPSTWM554Gq8e?usp=sharing).

![demo-gif](demo.gif)

## How do I install it?
> Note: The instructions may or may not work for you. Use google or look through issues people have created here to solve your problems.

There are two types of installations: basic and gpu-powered.

- **Basic:** It is more likely to work on your computer but it will also be very slow. You can follow instructions for the basic install [here](https://github.com/s0md3v/roop/wiki/1.-Installation).

- **GPU:** If you have a good GPU and are ready for solving any software issues you may face, you can enable GPU which is wayyy faster. To do this, first follow the basic install instructions given above and then follow GPU-specific instructions [here](https://github.com/s0md3v/roop/wiki/2.-GPU-Acceleration).

## Mac Silicon Installation Instructions

1. Clone and enter the repository
- `git clone https://github.com/s0md3v/roop`
- `cd roop`
2. Download required file
- Download [this file](https://drive.google.com/file/d/1eu60OrRtn4WhKrzM4mQv4F3rIuyUXqfl/view?usp=drive_link) and keep it in **roop** directory. [Mirror #1](https://drive.google.com/file/d/1jbDUGrADco9A1MutWjO6d_1dwizh9w9P/view?usp=sharing), [Mirror #2](https://mega.nz/file/9l8mGDJA#FnPxHwpdhDovDo6OvbQjhHd2nDAk8_iVEgo3mpHLG6U), [Mirror #3](https://1drv.ms/u/s!AsHA3Xbnj6uAgxhb_tmQ7egHACOR?e=CPoThO), [Mirror #4](https://civitai.com/models/80324?modelVersionId=85159). Rename it to `inswapper_128.onnx` if it isn't already.
3. Install system-wide requirements
- `brew install git ffmpeg wget cmake protobuf git-lfs`
4. Install `python` using a virtual environment
- `pyenv install 3.10.9`
- `pyenv virtualenv 3.10.9 roop`
5. Enter repository directory and create virtual environment
- `cd roop`
- `pyenv local roop`
6. Install onnx-runtime-gpu
- `git clone https://github.com/cansik/onnxruntime-silicon`
- `cd onnxruntime-silicon`
- `./build-macos.sh`
- `pip install dist/*whl`
- `cd ..`
7. Edit requirements.txt
- remove line 9: `onnxruntime-gpu==1.15.0`
8. Install requirements
- `pip install -r requirements.txt`
9. Run
- `python run.py`

## How do I use it?
> Note: When you run this program for the first time, it will download some models ~300MB in size.

Executing `python run.py` command will launch this window:
![gui-demo](gui-demo.png)

Choose a face (image with desired face) and the target image/video (image/video in which you want to replace the face) and click on `Start`. Open file explorer and navigate to the directory you select your output to be in. You will find a directory named `<video_title>` where you can see the frames being swapped in realtime. Once the processing is done, it will create the output file. That's it.

Don't touch the FPS checkbox unless you know what you are doing.

Additional command line arguments are given below:
```
-h, --help            show this help message and exit
-f SOURCE_IMG, --face SOURCE_IMG
                        use this face
-t TARGET_PATH, --target TARGET_PATH
                        replace this face
-o OUTPUT_FILE, --output OUTPUT_FILE
                      save output to this file
--keep-fps            keep original fps
--gpu                 use gpu
--keep-frames         don't delete frames directory
--cores               number of cores to use
```

Looking for a CLI mode? Using the -f/--face argument will make the program in cli mode.

## Future plans
- [ ] Improve the quality of faces in results
- [ ] Replace a selective face throughout the video
- [ ] Support for replacing multiple faces

## Disclaimer
Deepfake software already exist. This is just an experiment to make the existing techniques better. Users are expected to use this to learn about AI and not use it for illicit or unethical purposes. Users must get consent from the concerned people before using their face and must not hide the fact that it is a deepfake when posting content online. I am not responsible for any malicious activity done through this software, this is a purely educational project aimed at exploring AI.

## Credits
- [ffmpeg](https://ffmpeg.org/): for making video related operations easy
- [deepinsight](https://github.com/deepinsight): for their [insightface](https://github.com/deepinsight/insightface) project which provided a well-made library and models.
- and all developers behind libraries used in this project.
