FROM gdal:ubuntu-small-3.4.0-ecw-5.5.0
RUN mkdir /vsis3 && chmod -R 777 /vsis3
RUN mkdir /app
WORKDIR /app
ENV PYTHONPATH=${PYTHONPATH}:'/app'
RUN apt-get update -y \
    && apt-get install -y python3-pip
RUN apt-get update \
    &&  pip3 install --upgrade pip
COPY requirements.txt ./
RUN pip3 install -r ./requirements.txt -t /app
RUN apt-get remove -y python3-pip
COPY . .
RUN chmod +x start.sh
RUN python3 /app/confd/generate-config.py --environment production

RUN chmod -R 777 ./confd && mkdir -p config && chmod 777 ./config && \
    mkdir vrt_outputs && chmod -R 777 ./vrt_outputs && \
    mkdir -p logs && chmod -R 777 logs
CMD ["sh", "start.sh"]
