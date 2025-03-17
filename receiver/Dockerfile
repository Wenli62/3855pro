FROM python:3
LABEL maintainer="wxu62@my.bcit.ca"

RUN mkdir /receiver
RUN mkdir /receiver/log

COPY ./requirements.txt /receiver/requirements.txt

WORKDIR /receiver

RUN pip3 install -r requirements.txt
RUN pip3 install --upgrade setuptools
COPY . /receiver

RUN chown -R nobody:nogroup /receiver
USER nobody

EXPOSE 8080

ENTRYPOINT ["python3"]

CMD ["app.py"]