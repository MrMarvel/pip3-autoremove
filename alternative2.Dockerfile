FROM ubuntu:noble


RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    export DEBIAN_FRONTEND=noninteractive && \
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc && \
    echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc && \
    . ~/.bashrc && \
    apt update && apt-get --no-install-recommends -y install \
    make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev curl git \
    libncursesw5-dev xz-utils tk-dev libxml2-dev  \
    libxmlsec1-dev libffi-dev liblzma-dev && \
    apt-get --no-install-recommends -y install \
    ca-certificates && \
    curl -fsSL https://pyenv.run | bash && \
    to_install=$(for i in 2.7 $(for i in $(seq 6 13); do echo 3.$i; done); \
    do echo $i; done) && \
    echo Versions to install: $to_install && \
    for version in $to_install; do \
        echo "Installing Python $version job start"; \
        PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install $version & \
    done && \
    wait && \
    pyenv global 3.13 && \
    apt-mark auto make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev curl git \
    libncursesw5-dev xz-utils tk-dev libxml2-dev  \
    libxmlsec1-dev libffi-dev liblzma-dev && \
    apt-mark auto ca-certificates && \
    apt-get --no-install-recommends --purge -y autoremove

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get --no-install-recommends -y install \
    tox nox ncdu nano && \
    echo 'export PATH="$PYENV_ROOT/shims:$PATH"' >> ~/.bashrc && \
    . ~/.bashrc && \
    to_install=$(for i in 2.7 $(for i in $(seq 6 13); do echo 3.$i; done); \
    do echo $i; done) && \
    pyenv global $to_install && \
    apt-get --no-install-recommends --purge -y autoremove

COPY . /app
WORKDIR /app

CMD ["tox"]