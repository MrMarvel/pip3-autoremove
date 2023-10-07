FROM robert96/tox:latest

COPY . /app
WORKDIR /app

CMD ["tox"]