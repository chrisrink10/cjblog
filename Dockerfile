FROM tiangolo/uwsgi-nginx-flask:flask-python3.5
MAINTAINER Chris Rink <chrisrink10@gmail.com>

RUN rm -rf /app/*

COPY ./cjblog /app/cjblog
COPY ./requirements.txt /tmp/requirements.txt
COPY ./bin /bin

RUN pip install -U pip
RUN pip install -r /tmp/requirements.txt