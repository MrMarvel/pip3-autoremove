FROM ubuntu:noble

ENV PYENV_ROOT="/root/.pyenv"
ENV PATH="$PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH"

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    export DEBIAN_FRONTEND=noninteractive && \
    apt update && apt-get --no-install-recommends -y install \
    make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev curl git \
    libncursesw5-dev xz-utils tk-dev libxml2-dev  \
    libxmlsec1-dev libffi-dev liblzma-dev && \
    apt-get --no-install-recommends -y install \
    ca-certificates && \
    curl -fsSL https://pyenv.run | bash && \
    to_install=$(for i in $(for i in $(seq 7 13); do echo 3.$i; done); \
    do echo $i; done) && \
    echo Versions to install: $to_install && \
    for version in $to_install; do \
        echo "Installing Python $version job start"; \
        PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install $version & \
    done && \
    wait && \
    pyenv global $to_install && \
    apt-mark auto make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev curl git \
    libncursesw5-dev xz-utils tk-dev libxml2-dev  \
    libxmlsec1-dev libffi-dev liblzma-dev && \
    apt-mark auto ca-certificates && \
    apt-get --no-install-recommends --purge -y autoremove

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get --no-install-recommends -y install \
    tox ncdu nano && \
    apt-get --no-install-recommends --purge -y autoremove

COPY . /app
WORKDIR /app


CMD ["tox"]