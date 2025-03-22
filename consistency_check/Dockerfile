FROM python:3
LABEL maintainer="wxu62@my.bcit.ca"

RUN mkdir /consistency_check
RUN mkdir /consistency_check/log
COPY ./requirements.txt /consistency_check/requirements.txt


WORKDIR /consistency_check

RUN pip3 install -r requirements.txt
RUN pip3 install --upgrade setuptools
COPY . /consistency_check

RUN chown -R nobody:nogroup /consistency_check
USER nobody

EXPOSE 8300

ENTRYPOINT ["python3"]

CMD ["app.py"]