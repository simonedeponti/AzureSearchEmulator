FROM python:3.5-alpine
MAINTAINER "Simone Deponti <simone.deponti@gmail.com>"

RUN mkdir -p /srv/webapp
RUN adduser -D -u 1000 webapp

WORKDIR /srv/webapp
ADD ./setup.py ./setup.py
ADD ./AzureSearchEmulator ./AzureSearchEmulator

RUN chown -R webapp:webapp /srv/webapp
RUN pip3 install -e .

USER webapp
EXPOSE 8080
CMD "AzureSearchEmulator"
