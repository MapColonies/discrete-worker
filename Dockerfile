FROM osgeo/gdal:alpine-normal-3.2.0
RUN mkdir /vsis3 && chmod 777 /vsis3
RUN mkdir /app
WORKDIR /app
ENV PYTHONPATH=${PYTHONPATH}:'/app'
RUN apk update -q --no-cache \
    && apk add -q --no-cache python3 py3-pip
COPY requirements.txt ./
RUN pip3 install -r ./requirements.txt -t /app
RUN apk del py3-pip
COPY . .
RUN chmod +x start.sh
RUN python3 /app/confd/generate-config.py --environment production

RUN chmod -R 777 ./confd && mkdir -p config && chmod 777 ./config && \
    mkdir vrt_outputs && chmod -R 777 ./vrt_outputs && \
    mkdir -p logs && chmod -R 777 logs
CMD ["sh", "start.sh"]
