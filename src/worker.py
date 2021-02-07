from osgeo import gdal, ogr
from os import path, remove as remove_file
from logger.jsonLogger import Logger
from config import read_json
from gdal2tiles import generate_tiles
from utilities import get_tiles_location
from errors.vrt_errors import VRTError
import src.db_connector as db_connector
import worker_constants
import requests
import shutil


class Worker:
    def __init__(self):
        self.log = Logger.get_logger_instance()
        config_path = path.join(path.dirname(__file__),
                                '../config/production.json')
        self.__config = read_json(config_path)
        self.tiles_folder_location = get_tiles_location()

    def vrt_file_location(self, discrete_id):
        output_file_name = '{0}.vrt'.format(discrete_id)
        output_path = path.join(worker_constants.VRT_OUTPUT_FOLDER_NAME, output_file_name) 
        return output_path

    def remove_vrt_file(self, discrete_id, zoom_levels):
        vrt_path = self.vrt_file_location(discrete_id)
        self.log.info('Removing vrt file from path "{0}" on ID {1} with zoom-levels {2}'.format(vrt_path, discrete_id, zoom_levels))
        remove_file(vrt_path)

    def remove_s3_temp_files(self, discrete_id, zoom_levels):
        tiles_location = '{0}/{1}'.format(self.tiles_folder_location, discrete_id)
        self.log.info('Removing folder {0} on ID {1} with zoom-levels {2}'.format(tiles_location, discrete_id, zoom_levels))
        shutil.rmtree(tiles_location)

    def validate_data(self, task_values):
        if (task_values['min_zoom_level'] > task_values['max_zoom_level']):
            raise ValueError('Minimum zoom level cannot be greater than maximum zoom level')


    def buildvrt_utility(self, task_values):
        zoom_levels = '{0}-{1}'.format(task_values["min_zoom_level"], task_values["max_zoom_level"])
        discrete_id = task_values["discrete_id"]
        task_id = task_values["task_id"]
        version = task_values["version"]
        
        discrete_layer = db_connector.get_discrete_layer(discrete_id, version)

        vrt_config = {
            'VRTNodata': self.__config["gdal"]["vrt"]["no_data"],
            'outputSRS': self.__config["gdal"]["vrt"]["output_srs"],
            'resampleAlg': self.__config["gdal"]["vrt"]["resample_algo"]
        }

        self.log.info("Starting process GDAL-BUILD-VRT on taskID: {0} discreteID: {1}, version: {2} and zoom-levels: {3}"
                        .format(task_id, discrete_id, version, zoom_levels))
        vrt_result = gdal.BuildVRT(self.vrt_file_location(discrete_id), discrete_layer["metadata"]["tiffs"], **vrt_config)

        if vrt_result != None:
            vrt_result.FlushCache()
            vrt_result = None
        else:
            raise VRTError("Could not create VRT File")


    def gdal2tiles_utility(self, task_values):
        zoom_levels = '{0}-{1}'.format(task_values["min_zoom_level"], task_values["max_zoom_level"])
        discrete_id = task_values["discrete_id"]
        task_id = task_values["task_id"]
        version = task_values["version"]

        options = {
            'resampling': 'bilinear',
            'tmscompatible': True,
            'profile': 'geodetic',
            'zoom': zoom_levels
        }

        tiles_path = '{0}/{1}/{2}'.format(self.tiles_folder_location, discrete_id, version)

        self.log.info("Starting process GDAL2TILES on taskID: {0} discreteID: {1}, version: {2} and zoom-levels: {3}"
                            .format(task_id, discrete_id, version, zoom_levels))
        generate_tiles(self.vrt_file_location(discrete_id), tiles_path, **options)
