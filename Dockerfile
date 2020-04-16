FROM python:3.8-buster

RUN apt-get update \
    && apt-get --yes --no-install-recommends install pipenv \
    && apt-get --yes autoremove \
    && apt-get autoclean \
    && rm -rf /var/lib/apt/lists/*

COPY . /workdir/
WORKDIR /workdir

RUN pipenv --python 3.8 && pipenv install --dev

RUN pipenv run pyinstaller \
    --paths "$(pipenv --venv)" \
    --clean \
    --onefile \
    swarm-janitor.py


FROM debian:buster-slim

RUN apt-get update \
    && apt-get --yes --no-install-recommends install curl \
    && apt-get --yes autoremove \
    && apt-get autoclean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=0 /workdir/dist/swarm-janitor swarm-janitor

EXPOSE 2380
CMD ["/app/swarm-janitor"]
