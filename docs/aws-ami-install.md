
If you are tired of making GPU work, you can just an AWS instance with GPU. AWS already provides AMI with NVIDIA driver installed. Here are high level steps:


# AWS Marketplace. 
Go to AWS Marketplace and search for `Amazon Linux 2 AMI with NVIDIA TESLA GPU Driver`. Click on subscribe and follow instructions. Note that there is no charge for the AMI itself, you pay regular ec2 instance price. 
G4 instance are pretty cheap and when you launch them, you can select spot instance so that it is even cheaper. Needless to say, these instance can be terminated any time so plan accordingly. Once you have AWS instance up and running, install software:


# FFMPEG install 

```bash
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar -xf ffmpeg-release-amd64-static.tar.xz
sudo mv ffmpeg-6.0-amd64-static/ffmpeg /usr/local/bin/
```

# Conda 
This is required for a more modern python version (note that I am not using sudo here). The pre-installed version that comes with AMI is quite old. 

```bash
wget https://repo.anaconda.com/archive/Anaconda3-2023.03-1-Linux-x86_64.sh
sh Anaconda3-2023.03-1-Linux-x86_64.sh
```

When asked - 
```
Do you wish the installer to initialize Anaconda3
by running conda init? [yes|no]

```

say `yes`. It will tell you to exit the shell and re-login. You don't need to do that, just run command `source ~/.bashrc`, that has same effect 

you should see your shell prompt with (base) prefix now. Confirm you have right python version by running python --version command. I got `Python 3.10.9`, that's recent enough.


## install git and download root
```
sudo yum install git -y 
git clone https://github.com/s0md3v/roop.git ; cd roop
```

# install dependencies
`python -m pip install -r requirements.txt`

# upload model file
`scp /path/to/inswapper_128.onnx ec2-user@<ec2-public-ip>:/home/ec2-user/roop/`

you are all set. 

