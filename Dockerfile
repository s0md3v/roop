FROM python:3.9

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    ffmpeg

RUN pip install --upgrade pip

# CMD [ "/bin/bash" ]
CMD ["tail", "-f", "/dev/null"]
