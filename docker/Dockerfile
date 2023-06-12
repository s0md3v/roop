FROM python:3.10

RUN apt-get update && apt-get install -y \
	ffmpeg

RUN git clone https://github.com/s0md3v/roop.git /roop

RUN pip install -r roop/requirements.txt

ENTRYPOINT ["python", "/roop/run.py"]
