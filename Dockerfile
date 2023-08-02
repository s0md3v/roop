FROM python:3.10

ENV EXECUTION_PROVIDER=CPU

RUN apt-get update && apt-get install -y ffmpeg
RUN pip install --upgrade pip
#RUN git clone https://github.com/s0md3v/roop.git /roop

RUN git clone https://github.com/danikhani/roop.git -b docker /roop
RUN pip install -r roop/requirements.txt
RUN pip install -r roop/requirements-docker.txt

CMD ["python", "/roop/api.py"]