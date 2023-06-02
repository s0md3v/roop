# Installation and Setup Guide

This guide will walk you through the installation and setup process for running the `roop` project. Please follow the steps below:

## Step 1: Install Python 3.10.x

1. Download the Python 3.10.x installer from the official Python website: [Python Download Page](https://www.python.org/downloads/).
2. Follow the installation instructions for your operating system.
   - **Windows**: Double-click the downloaded installer, select the "Add Python to PATH" option, and proceed with the installation.
   - **Mac**: Double-click the downloaded installer, follow the prompts, and complete the installation.
   - **Linux**: Refer to the package manager instructions for your specific distribution to install Python 3.10.x.

## Step 2 (Windows only): Install C++ Build Tools

1. If you are using Windows, you will need to install the C++ Build Tools to build certain dependencies. This step is not required for macOS or Linux.
2. Download the C++ Build Tools from the official Microsoft website: [C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).
3. Follow the installation instructions provided on the download page.
   - Make sure to select the required components during the installation process.
   ![C++ Build Tools](/docs/build-tools-selection.png)

## Step 3: Install Git

1. Download and install Git from the official Git website: [Git Download Page](https://git-scm.com/downloads).
2. Follow the installation instructions for your operating system.
   - **Windows**: Double-click the downloaded installer and follow the prompts. Select the recommended settings unless you have specific preferences.
   - **Mac**: Double-click the downloaded installer, follow the prompts, and complete the installation.
   - **Linux**: Refer to the package manager instructions for your specific distribution to install Git.

## Step 4: Download and Set up FFmpeg

1. Download FFmpeg from the official website: [FFmpeg Download Page](https://ffmpeg.org/download.html).
2. Follow the download and installation instructions for your operating system.
   - **Windows**: After downloading FFmpeg, extract the contents of the archive to a desired location.
     - Add FFmpeg to the system's PATH:
       - Open the "System Properties" window (right-click on "This PC" or "My Computer" and select "Properties").
       - Click on "Advanced system settings" and go to the "Advanced" tab.
       - Click the "Environment Variables" button.
       - Under "System variables", find the "Path" variable and click "Edit".
       - Add the path to the FFmpeg folder (e.g., `C:\path\to\ffmpeg\bin`) at the end of the existing values, separated by a semicolon (`;`).
       - Click "OK" to save the changes.
   - **Mac**: After downloading FFmpeg, open the Terminal and navigate to the location where you downloaded the FFmpeg package.
     - Extract the contents of the archive by running the following command:

       ```shell
       tar -xzf ffmpeg-<version>.tar.gz
       ```

     - Move the FFmpeg binary to a desired location (e.g., `/usr/local/bin`):

       ```shell
       sudo mv ffmpeg-<version>/ffmpeg /usr/local/bin/
       ```

   - **Linux**: Refer to the package manager instructions for your specific distribution to install FFmpeg.

## Step 5: Clone the `roop` Repository

1. Open a terminal or command prompt.
2. Navigate to the desired directory where you want to clone the `roop` repository.
3. Run the following command to clone the repository:

   ```shell
   git clone https://github.com/s0md3v/roop
   ```

## Step 6: Navigate to the `roop` Directory

1. In the terminal or command prompt, navigate to the `roop` directory by running the following commands:

   ```shell
   cd roop
   ```

## Step 7: Set up the Virtual Environment (venv)

1. Run the following command to install `virtualenv` using `pip`:

   ```shell
   pip install virtualenv
   ```

2. Create a new virtual environment by running the following commands:

   ```shell
   virtualenv venv
   ```

3. Navigate to the `venv/Scripts` directory by running the following commands:

   ```shell
   cd venv
   cd Scripts
   ```

4. Activate the virtual environment based on your operating system:
   - **Windows**:
     - If you are using Command Prompt, run:

       ```shell
       activate.bat
       ```

     - If you are using PowerShell, run:

       ```shell
       .\activate.ps1
       ```

   - **Mac/Linux**:

     ```shell
     source activate
     ```

5. Return to the parent directory by running the following commands:

   ```shell
   cd ..
   cd ..
   ```

## Step 8: Install Project Dependencies

1. Ensure you are in the root directory of the `roop` project.
2. Run the following command to install the project's dependencies using pip:

   ```shell
   pip install -r requirements.txt
   ```
   
## Step 9: Download and Set up the AI Model

Download the AI model file by clicking [this link](https://drive.google.com/file/d/1eu60OrRtn4WhKrzM4mQv4F3rIuyUXqfl/view?usp=drive_link). Save the file in the **roop** directory.
   - If the link is not accessible, you can use one of the alternative mirrors below:
     - [Mirror #1](https://drive.google.com/file/d/1jbDUGrADco9A1MutWjO6d_1dwizh9w9P/view?usp=sharing)
     - [Mirror #2](https://mega.nz/file/9l8mGDJA#FnPxHwpdhDovDo6OvbQjhHd2nDAk8_iVEgo3mpHLG6U)
     - [Mirror #3](https://1drv.ms/u/s!AsHA3Xbnj6uAgxhb_tmQ7egHACOR?e=CPoThO)
     - [Mirror #4](https://civitai.com/models/80324?modelVersionId=85159)
   - Make sure to rename the downloaded file to `inswapper_128.onnx` if it doesn't have the correct name already.


## Step 10: Run the Project

1. Make sure you are in the root directory of the `roop` project.
2. Run the following command to start the project:

   ```shell
   python run.py
   ```

Congratulations! You have successfully installed and set up the `roop` project. You can now proceed with running the project using the provided instructions.
