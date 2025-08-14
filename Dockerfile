FROM robert96/tox:latest

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update && apt-get --no-install-recommends -y install \
    ncdu nano && \
    apt-get --no-install-recommends --purge -y autoremove

COPY . /app
WORKDIR /app

CMD ["tox"]