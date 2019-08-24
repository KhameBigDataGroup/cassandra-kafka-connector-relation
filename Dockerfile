FROM python:3
LABEL maintainer="amir77ni@gmail.com"

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN CASS_DRIVER_BUILD_CONCURRENCY=8 pip install --no-cache-dir -r requirements.txt

COPY . .

ENV BOOSTRAP_SERVER "172.17.0.1:9092"
ENV CASSANDRA_HOST "172.17.0.1"

CMD [ "python", "-u", "./script.py" ]
