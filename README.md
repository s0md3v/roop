# Roop - Face Replacement Software

Roop is a face replacement software that allows you to replace faces in videos with a face of your choice using a single image. With Roop, you can create deepfake videos without the need for a dataset or training. Please note that this software is a hobby project created for learning purposes and should be used responsibly. Before using someone's face, ensure you have their consent and do not mislead others about the nature of the content. The developer of Roop is not responsible for any misuse or malicious behavior by end-users.

## Demo

Check out some demos of Roop in action: [Demo Videos](https://drive.google.com/drive/folders/1KHv8n_rd3Lcr2v7jBq1yPSTWM554Gq8e?usp=sharing)

![Demo GIF](/docs/demo.gif)

Check out the latest video made by our test CI below:

![Demo Video](/docs/examples/latest-test.mp4)

## Disclaimer

Please be aware that there are more advanced deepfake software available. Roop is a personal project created to explore AI technologies. The software includes a built-in check to prevent inappropriate media from being processed.

## Installation

To install Roop, there are two types of installations available: basic and GPU-powered.

- **Basic Installation:** This option is more likely to work on most computers but may be slower. Follow the instructions for the basic install [here](/docs/INSTALLATION.md).

- **GPU Installation:** If you have a powerful GPU and are comfortable troubleshooting potential software issues, you can enable GPU acceleration for faster processing. Start by following the basic installation instructions above, and then refer to the GPU-specific instructions [~~here~~](https://github.com/s0md3v/roop/wiki/2.-GPU-Acceleration). **Updated documentation coming soon!**

## Usage

> Note: When running Roop for the first time, it will download models of approximately 300MB in size.

1. Execute the following command to launch Roop:

   ```shell
   python run.py
   ```

2. The Roop graphical user interface (GUI) window will appear as shown below:
   ![GUI Demo](/docs/gui-demo.png)

3. Select a face image (the image with the desired face) and a target image/video (the image/video in which you want to replace the face) using the provided options.

4. Click on the `Start` button to begin the face replacement process.

5. Open the file explorer and navigate to the directory where you selected the output to be saved. You will find a directory named `<video_title>` where you can observe the frames being swapped in real-time. Once the processing is complete, Roop will create the output file.

> Caution: Unless you are familiar with the workings of the software, avoid modifying the FPS checkbox.

Additional command-line arguments for Roop are as follows:

```shell
Options:
  -h, --help                   Show this help message and exit
  -f SOURCE_IMG,
     --face SOURCE_IMG         Use this face
  -t TARGET_PATH,
     --target TARGET_PATH      Replace this face
  -o OUTPUT_FILE,
     --output OUTPUT_FILE      Save output to this file
  --gpu                        Use GPU
  --keep-fps                   Maintain original FPS
  --keep-frames                Keep frames directory
  --max-memory MAX_MEMORY      Maximum amount of RAM in GB to be used
  --max-cores CORES_COUNT      Number of cores to be used for CPU mode
  --all-faces                  Swap all faces in frame
```

If you prefer to use the CLI mode, you can use the `-f/--face` argument to run the program in CLI mode.

## Future Plans

The developer has outlined the following future plans for Roop:

- [ ] Improve the quality of faces in the results
- [ ] Enable selective face replacement throughout the video
- [ ] Support for replacing multiple faces

## Credits

Roop acknowledges the following projects and libraries for their contributions:

- [FFmpeg](https://ffmpeg.org/): For simplifying video-related operations
- [Deepinsight](https://github.com/deepinsight): For their [InsightFace](https://github.com/deepinsight/insightface) project, providing a well-made library and models
- All developers behind the libraries utilized in this project
