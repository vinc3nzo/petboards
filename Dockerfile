FROM alpine:3.17

COPY requirements.txt .

RUN mkdir -p /opt/petboards/petboards && \
    mkdir -p /opt/petboards/data && \
    apk update && \
    apk add 'python3>3.10.9' 'py3-pip<23.1' && \
    pip3 install -r ./requirements.txt && \
    rm ./requirements.txt

COPY ./petboards/petboards /opt/petboards/petboards

WORKDIR /opt/petboards

CMD [ "gunicorn", "-b", "0.0.0.0:8000", "petboards.start:app" ]