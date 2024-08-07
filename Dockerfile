# 1. if you're using rancher desktop on Linux:
# nerdctl -n k8s.io build -f Dockerfile -t mcr-focal-fixed .
# 2. OR if you're using Docker Desktop:
# docker build -f Dockerfile -t mcr-focal-fixed .
FROM mcr.microsoft.com/vscode/devcontainers/base:0-focal

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
RUN unset DISPLAY
ENV DEBIAN_FRONTEND=noninteractive

# switch to automatic mirror select mode, makes building much faster down here
RUN sed -i 's http://archive.ubuntu.com/ubuntu/ mirror://mirrors.ubuntu.com/mirrors.txt ' /etc/apt/sources.list

RUN apt -y update && apt -y install python3.8-venv python3.9-full python3.9-dev build-essential iputils-ping libpq-dev postgresql-client

USER vscode

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python3 -
