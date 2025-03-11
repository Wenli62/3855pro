FROM python:3
LABEL maintainer="wxu62@my.bcit.ca"

RUN mkdir /processing
RUN mkdir /processing/log
COPY ./requirements.txt /processing/requirements.txt


WORKDIR /processing

RUN pip3 install -r requirements.txt
RUN pip3 install --upgrade setuptools
COPY . /processing

RUN chown -R nobody:nogroup /processing
RUN chmod -R 777 /processing/log
USER nobody

EXPOSE 8100

ENTRYPOINT ["python3"]

CMD ["app.py"]