FROM python:3.11
LABEL maintainer="wxu62@my.bcit.ca"

RUN mkdir /storage
RUN mkdir /storage/log


COPY ./requirements.txt /storage/requirements.txt

WORKDIR /storage

RUN pip3 install -r requirements.txt
RUN pip3 install --upgrade setuptools
COPY . /storage

RUN chown -R nobody:nogroup /storage
RUN chmod -R 777 /storage/log
USER nobody

EXPOSE 8090

# ENTRYPOINT ["python3"]

# CMD ["app.py"]