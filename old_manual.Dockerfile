FROM ubuntu:noble

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    export DEBIAN_FRONTEND=noninteractive && \
    apt update && apt-get --no-install-recommends -y install \
    software-properties-common wget ncdu nano && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt update && apt-get --no-install-recommends -y install \
    python3.5 python3.6 python3.7 python3.8 python3.9 python3.10 python3.11 python3.12 \
    python3.13 python3-pip && \
    mkdir -p /tmp/python2deb && \
    wget --directory-prefix /tmp/python2deb \
    http://archive.ubuntu.com/ubuntu/pool/universe/p/python2.7/libpython2.7-minimal_2.7.18-13ubuntu1.5_amd64.deb \
    http://archive.ubuntu.com/ubuntu/pool/universe/p/python2.7/python2.7-minimal_2.7.18-13ubuntu1.5_amd64.deb \
    http://archive.ubuntu.com/ubuntu/pool/universe/p/python2.7/libpython2.7-stdlib_2.7.18-13ubuntu1.5_amd64.deb \
    http://archive.ubuntu.com/ubuntu/pool/universe/p/python2.7/python2.7_2.7.18-13ubuntu1.5_amd64.deb && \
    apt-get --no-install-recommends -y install /tmp/python2deb/*.deb && rm -rf /tmp/* && \
    apt-get --no-install-recommends -y install \
    tox && \
    apt-mark auto \
    software-properties-common wget && \
    apt-get --no-install-recommends --purge -y autoremove

COPY . /app
WORKDIR /app

CMD ["tox"]