from osgeo import gdal, ogr
from os import path, remove as remove_file
from logger.jsonLogger import Logger
from config import read_json
from gdal2tiles import generate_tiles
from model.enums.storage_provider import StorageProvider
import worker_constants
import requests
import shutil


class Worker:
    def __init__(self):
        self.log = Logger.get_logger_instance()
        config_path = path.join(path.dirname(__file__),
                                '../config/production.json')
        self.__config = read_json(config_path)

    def tiles_location(self):
        storage_provider = self.__config['storage_provider'].upper()

        if (storage_provider == StorageProvider.FS):
            return self.__config["fs"]["internal_outputs_path"]

        elif (storage_provider == StorageProvider.S3):
            bucket = self.__config["s3"]["bucket"]
            s3_path = '/vsis3/{0}'.format(bucket)
            return s3_path

    def vrt_file_location(self, discrete_id):
        output_file_name = '{0}.vrt'.format(discrete_id)
        output_path = path.join(worker_constants.VRT_OUTPUT_FOLDER_NAME, output_file_name) 
        return output_path

    def remove_vrt_file(self, discrete_id, zoom_levels):
        vrt_path = self.vrt_file_location(discrete_id)
        self.log.info('Removing vrt file from path "{0}" on ID {1} with zoom-levels {2}'.format(vrt_path, discrete_id, zoom_levels))
        remove_file(vrt_path)

    def remove_s3_temp_files(self, discrete_id, zoom_levels):
        tiles_location = '{0}/{1}'.format(self.tiles_location(), discrete_id)
        self.log.info('Removing folder {0} on ID {1} with zoom-levels {2}'.format(tiles_location, discrete_id, zoom_levels))
        shutil.rmtree(tiles_location)


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
        zoom_levels = task_values["zoom_levels"]
        key = task_values["discrete_id"]

        options = {
            'resampling': 'bilinear',
            'tmscompatible': True,
            'profile': 'geodetic',
            'zoom': '{0}-{1}'.format(zoom_levels[0], zoom_levels[len(zoom_levels)-1])
        }

        tiles_path = '{0}/{1}'.format(self.tiles_location(), key)

        self.log.info("Starting process GDAL2TILES on ID: {0}, and zoom-levels: {1}".format(key, task_values["zoom_levels"]))
        generate_tiles(self.vrt_file_location(key), tiles_path, **options)
