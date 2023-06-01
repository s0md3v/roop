## Installation Guide

This guide provides step-by-step instructions for installing the necessary tools and dependencies to run the `roop` project. Please follow the instructions based on your operating system.

### 1. Install Python 3.10.x

Download and install Python 3.10.x from the official Python website:

[Download Python 3.10.x](https://www.python.org/downloads/)

Follow the installation instructions for your operating system.

### 2. Install C++ Build Tools (Windows only)

If you are using Windows, you will need to install C++ Build Tools, as certain Python packages require C++ compilation. Follow the steps below:

1. Visit [C++ Build Tools for Visual Studio](https://visualstudio.microsoft.com/visual-cpp-build-tools/).
2. Download the installer and run it.
3. During the installation process, select the necessary components for C++ build tools.
4. Complete the installation.

### 3. Install Git

Git is a version control system used to clone and manage code repositories. Install Git by following the instructions for your operating system:

**Windows:**

Download the Git installer from [Git for Windows](https://gitforwindows.org/). Run the installer and follow the on-screen instructions.

**Mac:**

Open the Terminal and run the following command:

```shell
brew install git
```

If Homebrew is not installed, visit the [Homebrew website](https://brew.sh/) to install it first.

**Linux:**

Open a terminal and run the appropriate package manager command for your distribution. For example, on Ubuntu, run:

```shell
sudo apt-get install git
```

### 4. Install FFmpeg

FFmpeg is a multimedia framework required by the `roop` project. Follow the steps below to install FFmpeg based on your operating system:

**Windows:**

1. Visit the [FFmpeg Download Page](https://ffmpeg.org/download.html).
2. Scroll down to the "Windows Builds" section.
3. Click on the "Static" link for the latest version.
4. Extract the downloaded ZIP file to a location on your computer.
5. Add the FFmpeg binary folder to your system's PATH environment variable:
   - Open the Start menu and search for "Environment Variables".
   - Click on "Edit the system environment variables".
   - In the System Properties window, click on the "Environment Variables" button.
   - In the "System variables" section, select the "Path" variable and click on "Edit".
   - Click on "New" and enter the path to the FFmpeg binary folder (e.g., `C:\path\to\ffmpeg\bin`).
   - Click "OK" to save the changes.
6. Close any open command prompt or terminal windows and reopen them for the changes to take effect.

**Mac:**

Open the Terminal and run the following command to install FFmpeg using Homebrew:

```shell
brew install ffmpeg
```

**Linux:**

Open a terminal and run the appropriate package manager command for your distribution. For example, on Ubuntu, run:

```shell
sudo apt-get install ffmpeg
```

### 5. Clone the `roop` Repository

Use Git to clone the `roop` repository by executing the following command in your preferred terminal:

```shell
git clone https://github.com/s0md3v/roop.git
```

This will create a local copy of the `roop` project on your machine.

### 6. Navigate to the `roop` Directory

Change your current directory to the `roop` directory by running the following command:

```shell
cd roop
```

### 7. Set up the Python Virtual Environment

Navigate to

 the virtual environment directory by executing the following command:

```shell
cd venv
```

Next, activate the virtual environment. The activation command varies depending on your operating system:

**Windows:**

```shell
Scripts\activate
```

**Mac/Linux:**

```shell
source bin/activate
```

### 8. Install Project Dependencies

With the virtual environment activated, install the project dependencies by executing the following command:

```shell
pip install -r requirements.txt
```

This will install all the necessary packages required by the `roop` project.

### 9. Run the Project

Finally, run the `roop` project by executing the following command:

```shell
python run.py
```

The project should now start running.

Congratulations! You have successfully installed and set up the `roop` project. Feel free to explore and utilize its features.
