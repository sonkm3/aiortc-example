FROM --platform=x86_64 debian:buster-slim
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update
RUN apt-get install -y --no-install-recommends \
    python3 python3-pip python3-dev \
    libopus-dev libsrtp2-dev libffi-dev libvpx-dev libssl-dev \
    libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libavfilter-dev libswscale-dev libswresample-dev\
    build-essential rustc cargo
#RUN pip3 install wheel setuptools
#RUN pip3 install aiohttp
#RUN pip3 install aiortc
RUN pip3 install virtualenv

WORKDIR /aiortc

RUN python3 -m virtualenv /aiortc/.virtualenv/aiortc
RUN /aiortc/.virtualenv/aiortc/bin/pip install aiohttp aiortc

COPY . /aiortc/
EXPOSE 8080