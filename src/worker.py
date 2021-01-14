from osgeo import gdal, ogr
from os import path
from logger.jsonLogger import Logger
from config import read_json
from gdal2tiles import generate_tiles
import requests


class Worker:
    def __init__(self):
        self.log = Logger.get_logger_instance()
        config_path = path.join(path.dirname(__file__),
                                '../config/production.json')
        self.__config = read_json(config_path)

    def set_gdal_s3(self):
        gdal.SetConfigOption('AWS_ACCESS_KEY_ID',
                             self.__config["s3"]["access_key_id"])
        gdal.SetConfigOption('AWS_SECRET_ACCESS_KEY',
                             self.__config["s3"]["secret_access_key"])
        gdal.SetConfigOption(
            'AWS_S3_ENDPOINT', self.__config["s3"]["endpoint_url"])
        gdal.SetConfigOption('AWS_HTTPS', self.__config["s3"]["ssl_enabled"])
        gdal.SetConfigOption('AWS_VIRTUAL_HOSTING', self.__config["s3"]["virtual_hosting"])
        gdal.SetConfigOption('CPL_VSIL_USE_TEMP_FILE_FOR_RANDOM_WRITE', 'YES')

    def buildvrt_utility(self, task_values):
        discrete_id = task_values["discrete_id"]
        get_discrete_by_id_url = f'{self.__config["discrete_storage"]["url"]}/{discrete_id}'
        discrete_layer = requests.get(url=get_discrete_by_id_url).json()

        vrt_config = {
            'VRTNodata': '0',
            'outputSRS': 'EPSG:4326',
            'resampleAlg': 'bilinear'
        }
        gdal.BuildVRT(f'{discrete_id}.vrt',
                      discrete_layer["tiffs"], **vrt_config)

    def gdal2tiles_utility(self, task_values):
        zoom_levels = task_values["zoom_levels"]
        key = task_values["discrete_id"]
        bucket = self.__config["s3"]["bucket"]
        generate_tiles(f'{key}.vrt', f'/vsis3/{bucket}',
                                zoom=f'{zoom_levels[0]}-{zoom_levels[len(zoom_levels)-1]}', 
                                resampling='bilinear', tmscompatible=True, profile='geodetic')
