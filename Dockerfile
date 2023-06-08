FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
	ffmpeg \
	nvidia-cudnn \
	python3 \
	python3-pip \
	python3-tk \
	python-is-python3

ADD requirements.txt .
RUN pip install -r requirements.txt

RUN mkdir -p /.config/matplotlib /.cache/matplotlib /.opennsfw2 && \
	chown -R 1000 /.config /.cache /.opennsfw2

CMD /bin/bash

WORKDIR /app
USER 1000
