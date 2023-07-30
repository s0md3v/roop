FROM python:3.10

ARG EXECUTION_PROVIDER=CPU

RUN apt-get update && apt-get install -y ffmpeg
RUN git clone https://github.com/s0md3v/roop.git /roop
RUN pip install -r roop/requirements-docker-cpu.txt

ENTRYPOINT ['python', '/roop/run_api.py']