FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

ARG DEFAULT_UID=1000
ARG DEFAULT_GID=1000
ENV DEFAULT_UID $DEFAULT_UID
ENV DEFAULT_GID $DEFAULT_GID
ENV PUSER "rooper"
ENV PGROUP "rooper"
ENV PUSER_PRIV_DROP true
ENV PUSER_RLIMIT_UNLOCK true

ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

ENV BUFFALO_L_URL "https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip"
# ENV INSWAPPER_128_URL "https://1drv.ms/u/s!AsHA3Xbnj6uAgxhb_tmQ7egHACOR?e=CPoThO"

COPY --chmod=644 ./inswapper_128.onnx /roop/inswapper_128.onnx
COPY ./requirements.txt /tmp/requirements.txt

RUN apt-get -q update && \
    apt-get install -q -y --no-install-recommends \
        build-essential \
        curl \
        ffmpeg \
        procps \
        psmisc \
        python3 \
        python3-dev \
        python3-pip \
        python3-setuptools \
        python3-tk \
        python3-wheel \
        sudo \
        tini \
        unzip \
        vim-tiny \
        zlib1g && \
    sed -i "s/set[[:space:]]*compatible/set nocompatible/g" /etc/vim/vimrc.tiny && \
    groupadd --gid ${DEFAULT_GID} ${PGROUP} && \
      useradd -m --uid ${DEFAULT_UID} --gid ${DEFAULT_GID} --home /home/${PUSER} ${PUSER} && \
      usermod -a -G tty ${PUSER} && \
      chsh -s /bin/bash ${PUSER} && \
      usermod -a -G sudo ${PUSER} && \
      echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers && \
    python3 -m pip install --index-url https://download.pytorch.org/whl/cu118 torch torchvision torchaudio && \
        python3 -m pip install onnxruntime-gpu && \
        python3 -m pip install -r /tmp/requirements.txt && \
    ln -s -r /usr/local/cuda-11.8/targets/x86_64-linux/lib/libnvrtc.so.11.2 /usr/local/cuda-11.8/targets/x86_64-linux/lib/libnvrtc.so.11 && \
        ln -s -r /usr/local/cuda-11.8/targets/x86_64-linux/lib/libnvrtc.so.11 /usr/local/cuda-11.8/targets/x86_64-linux/lib/libnvrtc.so && \
    mkdir -p /roop/roop /home/${PUSER}/.insightface/models/buffalo_l && \
        # curl -fsSL -o /roop/inswapper_128.onnx "${INSWAPPER_128_URL}" && \
        curl -fsSL -o /tmp/buffalo_l.zip "${BUFFALO_L_URL}" && \
        ln -s -r /roop/inswapper_128.onnx /roop/roopVideoFace_v10.onnx && \
        cd /home/${PUSER}/.insightface/models/buffalo_l && \
        unzip /tmp/buffalo_l.zip -d /home/${PUSER}/.insightface/models/buffalo_l && \
    chown -R ${PUSER}:${PGROUP} /home/${PUSER} /roop && \
    apt-get -y -q --allow-downgrades --allow-remove-essential --allow-change-held-packages --purge remove \
        build-essential \
        curl \
        python3-dev \
        unzip && \
    apt-get -y -q --allow-downgrades --allow-remove-essential --allow-change-held-packages autoremove && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY --chmod=755 ./*.py /roop/
COPY --chmod=755 ./roop/*.py /roop/roop
COPY --chmod=755 ./docker/docker-uid-gid-setup.sh /usr/local/bin/docker-uid-gid-setup.sh

ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility,video

WORKDIR /roop

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/docker-uid-gid-setup.sh"]
