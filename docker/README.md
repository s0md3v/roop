# Running roop in Docker

This is tested on a Linux host with CPU and Nvidia GPU.

There are two Dockerfiles:
- Dockerfile.nvidia supports both CPU and Nvidia GPU. The built image is about 20 GB.
- Dockerfile.cpu supports only CPU. The built image is about 12 GB.

## Prerequisites on the host for Nvidia GPU

You may skip this part if you only need CPU.

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

Build a Docker image using one of the Dockerfiles, depending on what you need:

```
docker/build.sh cpu
OR
docker/build.sh nvidia
```

## Usage with CPU

Run roop in Docker using either roop-cpu or roop-nvidia image:

```
docker run \
    --rm \
    -u `id -u`:`id -g` \
    -v `pwd`:/data \
    -v `pwd`/.cache:/cache \
    roop-cpu \
    -f '/data/.github/examples/face.jpg' \
    -t '/data/.github/examples/target.mp4' \
    -o '/data/demo-cpu.mp4'
```

## Usage with Nvidia GPU

Run roop in Docker using roop-nvidia image:

```
docker run \
    --rm \
    -u `id -u`:`id -g` \
    -v `pwd`:/data \
    -v `pwd`/.cache:/cache \
    --gpus all \
    roop-nvidia \
    --gpu-threads=1 \
    --gpu-vendor=nvidia \
    -f '/data/.github/examples/face.jpg' \
    -t '/data/.github/examples/target.mp4' \
    -o '/data/demo-nvidia.mp4'
```
