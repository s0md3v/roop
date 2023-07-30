FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

#RUN rm -rf /usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1 /usr/lib/x86_64-linux-gnu/libcuda.so.1
ARG EXECUTION_PROVIDER=GPU
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
	ffmpeg \
	git \
	nvidia-cudnn \
	python3 \
	python3-pip \
	python3-tk \
	python-is-python3

RUN git clone https://github.com/s0md3v/roop.git /roop

RUN pip install -r roop/requirements-docker-gpu.txt
#RUN pip uninstall onnxruntime onnxruntime-gpu
#RUN pip install onnxruntime-gpu==1.15.1
#ENTRYPOINT ['python', '/roop/run.py']


# fix modulus for wsl in windows:
# https://forums.developer.nvidia.com/t/wsl-modulus-docker-run-error-libnvidia-ml-so-1-file-exists-unknown/256058/5
RUN rm -rf \
    /usr/lib/x86_64-linux-gnu/libcuda.so* \
    /usr/lib/x86_64-linux-gnu/libnvcuvid.so* \
    /usr/lib/x86_64-linux-gnu/libnvidia-*.so* \
    /usr/local/cuda/compat/lib/*.515.65.01

ENTRYPOINT ['python', '/roop/run_api.py']