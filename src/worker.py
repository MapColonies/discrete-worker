from osgeo import gdal, ogr
from os import path, remove as remove_file
from logger.jsonLogger import Logger
from config import read_json
from gdal2tiles import generate_tiles
import requests
import shutil


class Worker:
    def __init__(self):
        self.log = Logger.get_logger_instance()
        config_path = path.join(path.dirname(__file__),
                                '../config/production.json')
        self.__config = read_json(config_path)

    def vrt_file_location(self, discrete_id):
        output_folder_name = self.__config["gdal"]["vrt"]["folder"]
        output_file_name = '{0}.vrt'.format(discrete_id)
        output_path = path.join(output_folder_name, output_file_name) 
        return output_path

    def remove_vrt_file(self, discrete_id, zoom_levels):
        vrt_path = self.vrt_file_location(discrete_id)
        self.log.info('Removing vrt file from path "{0}" on ID {1} with zoom-levels {2}'.format(vrt_path, discrete_id, zoom_levels))
        remove_file(vrt_path)

    def remove_s3_temp_files(self, discrete_id, zoom_levels):
        bucket = self.__config["s3"]["bucket"]
        s3_local_path = '/vsis3/{0}'.format(bucket)
        self.log.info('Removing folder {0} on ID {1} with zoom-levels {2}'.format(s3_local_path, discrete_id, zoom_levels))
        shutil.rmtree(s3_local_path)


    def set_gdal_s3(self):
        gdal.SetConfigOption('AWS_ACCESS_KEY_ID',
                             self.__config["s3"]["access_key_id"])
        gdal.SetConfigOption('AWS_SECRET_ACCESS_KEY',
                             self.__config["s3"]["secret_access_key"])
        gdal.SetConfigOption(
            'AWS_S3_ENDPOINT', self.__config["s3"]["endpoint_url"])
        gdal.SetConfigOption('AWS_HTTPS', self.__config["s3"]["ssl_enabled"])
        gdal.SetConfigOption('AWS_VIRTUAL_HOSTING',
                             self.__config["s3"]["virtual_hosting"])
        gdal.SetConfigOption('CPL_VSIL_USE_TEMP_FILE_FOR_RANDOM_WRITE', 'YES')

    def buildvrt_utility(self, task_values):
        key = task_values["discrete_id"]
        get_discrete_by_id_url = '{0}/{1}'.format(self.__config["discrete_storage"]["url"], key)
        discrete_layer = requests.get(url=get_discrete_by_id_url).json()

        vrt_config = {
            'VRTNodata': self.__config["gdal"]["vrt"]["no_data"],
            'outputSRS': self.__config["gdal"]["vrt"]["output_srs"],
            'resampleAlg': self.__config["gdal"]["vrt"]["resample_algo"]
        }

        self.log.info("Starting process GDAL-BUILD-VRT on ID: {0} and zoom-levels {1}".format(key, task_values["zoom_levels"]))
        gdal.BuildVRT(self.vrt_file_location(key), discrete_layer["tiffs"], **vrt_config)


    def gdal2tiles_utility(self, task_values):
        self.set_gdal_s3()
        zoom_levels = task_values["zoom_levels"]
        key = task_values["discrete_id"]

        options = {
            'resampling': 'bilinear',
            'tmscompatible': True,
            'profile': 'geodetic',
            'zoom': '{0}-{1}'.format(zoom_levels[0], zoom_levels[len(zoom_levels)-1])
        }

        bucket = self.__config["s3"]["bucket"]
        s3_path = '/vsis3/{0}/{1}'.format(bucket, key)

        self.log.info("Starting process GDAL2TILES on ID: {0}, and zoom-levels: {1}".format(key, task_values["zoom_levels"]))
        generate_tiles(self.vrt_file_location(key), s3_path, **options)
