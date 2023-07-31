FROM python:3.10

ENV EXECUTION_PROVIDER=CPU
ENV TEMP_FRAME_FORMAT=png
ENV TEMP_FRAME_QUALITY=0
ENV OUTPUT_VIDEO_QUALITY=0

RUN apt-get update && apt-get install -y ffmpeg
RUN pip install --upgrade pip
#RUN git clone https://github.com/s0md3v/roop.git /roop
RUN ls
RUN git clone https://github.com/danikhani/roop.git -b docker /roop
RUN pip install -r roop/requirements-docker.txt

RUN ls
RUN pwd
RUN rm -rf /roop

RUN git clone https://github.com/danikhani/roop.git -b docker /roop
CMD ["python", "/roop/api.py"]