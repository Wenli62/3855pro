FROM python:3
LABEL maintainer="wxu62@my.bcit.ca"

RUN mkdir /analyzer
RUN mkdir /analyzer/log

COPY ./requirements.txt /analyzer/requirements.txt

WORKDIR /analyzer

RUN pip3 install -r requirements.txt
RUN pip3 install --upgrade setuptools
COPY . /analyzer

RUN chown -R nobody:nogroup /analyzer
USER nobody

EXPOSE 8200

ENTRYPOINT ["python3"]

CMD ["app.py"]