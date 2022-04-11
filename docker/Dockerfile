FROM python:3.8-slim

RUN apt update && apt upgrade

WORKDIR /usr/src/app
COPY docker/requirements.txt ./requirements.txt
COPY . ./player-session-service
RUN pip3 install --no-cache-dir -r ./requirements.txt


