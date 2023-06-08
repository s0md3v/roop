# Running roop in Docker

This is tested on a Linux host with an Nvidia GPU.

## Prerequisites on the host

1. Install Nvidia drivers:
    a) Install automatically:
        ```
        ubuntu-drivers autoinstall
        ```
    b) Install specific version:
        ```
        apt install nvidia-driver-530
        ```
2. Install and enable Nvidia Container Toolkit:
```
apt install nvidia-docker2
nvidia-ctk runtime configure
systemctl restart docker
```
3. Test if GPU works in the container:
```
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

## Building the image

1. Build the Docker image:
```
docker-compose build
```
2. Test if GPU works in the container:
```
docker-compose run roop nvidia-smi
```

## Usage

Run roop in Docker:

```
docker-compose run roop python run.py --gpu-threads=1 --gpu-vendor=nvidia -f '/app/.github/examples/face.jpg' -t '/app/.github/examples/target.mp4' -o '/app/demo.mp4'
```
