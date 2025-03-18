FROM nginx

RUN apt-get update && apt-get install -y gettext-base

COPY . /usr/share/nginx/html

CMD envsubst < /usr/share/nginx/html/updateStats.js > /usr/share/nginx/html/updateStats.js && \
    nginx -g 'daemon off;'



