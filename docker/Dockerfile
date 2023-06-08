FROM python:3.11

RUN apt-get update && apt-get install -y \
	ffmpeg

RUN git clone https://github.com/s0md3v/roop.git /app

RUN cd /app && pip install -r requirements.txt

ENTRYPOINT ["python", "/app/run.py"]
