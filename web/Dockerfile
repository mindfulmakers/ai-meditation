FROM python:3.13-slim

EXPOSE 8000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install requirements
RUN apt-get update && apt-get install -y ffmpeg curl postgresql-client git

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

ARG GH_PAT
ENV GH_PAT=$GH_PAT
COPY nocache.txt /tmp/nocache.txt
COPY app_requirements_docker.txt .

# Configure git and install site requirements
RUN git config --global url."https://${GH_PAT}:x-oauth-basic@github.com/".insteadOf "https://github.com/" && \
    pip install -r app_requirements_docker.txt && \
    git config --global --unset url."https://${GH_PAT}:x-oauth-basic@github.com/".insteadOf

WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

