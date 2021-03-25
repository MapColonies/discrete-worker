from osgeo import gdal, ogr
from os import path, remove as remove_file
from logger.jsonLogger import Logger
from config import Config
from gdal2tiles import generate_tiles
from utilities import get_tiles_location
from errors.vrt_errors import VRTError
import src.request_connector as request_connector
import constants
import requests
import shutil

class Worker:
    def __init__(self):
        self.log = Logger.get_logger_instance()
        self.__config = Config.get_config_instance()
        self.tiles_folder_location = get_tiles_location()

    def vrt_file_location(self, discrete_id):
        output_file_name = '{0}.vrt'.format(discrete_id)
        output_path = path.join(constants.VRT_OUTPUT_FOLDER_NAME, output_file_name) 
        return output_path

    def remove_vrt_file(self, discrete_id, job_id, task_id, zoom_levels):
        vrt_path = self.vrt_file_location(discrete_id)
        self.log.info('Removing vrt file from path "{0}", jobID: {1}, taskID: {2}, discreteID {3}, with zoom-levels {4}'.format(vrt_path, job_id, task_id, discrete_id, zoom_levels))
        remove_file(vrt_path)

    def remove_s3_temp_files(self, discrete_id, job_id, task_id, zoom_levels):
        tiles_location = '{0}/{1}'.format(self.tiles_folder_location, discrete_id)
        self.log.info('Removing folder {0} on ID {1} with zoom-levels {2}'.format(tiles_location, job_id, task_id, discrete_id, zoom_levels))
        shutil.rmtree(tiles_location)

    def buildvrt_utility(self, job_id, task_id, discrete_id, version, zoom_levels):
        
        job_data = request_connector.get_job_data(job_id)
        if not (job_data["parameters"] and job_data["parameters"]["fileUris"]):
            raise VRTError("jobData didn't have fileUris field, for jobID: {0} taskID: {1} discreteID: {2}, version: {3} jobData: {4}"
            .format(job_id, task_id, discrete_id, version, job_data))

        vrt_config = {
            'VRTNodata': self.__config["gdal"]["vrt"]["no_data"],
            'outputSRS': self.__config["gdal"]["vrt"]["output_srs"],
            'resampleAlg': self.__config["gdal"]["vrt"]["resample_algo"]
        }

        self.log.info("Starting process GDAL-BUILD-VRT on jobID: {0} taskID: {1} discreteID: {2}, version: {3} and zoom-levels: {4}"
                        .format(job_id, task_id, discrete_id, version, zoom_levels))
        vrt_result = gdal.BuildVRT(self.vrt_file_location(discrete_id), job_data["parameters"]["fileUris"], **vrt_config)

        if vrt_result != None:
            vrt_result.FlushCache()
            vrt_result = None
        else:
            raise VRTError("Could not create VRT File")


    def gdal2tiles_utility(self, job_id, task_id, discrete_id, version, zoom_levels):

        options = {
            'resampling': self.__config['gdal']['resampling'],
            'tmscompatible': self.__config['gdal']['tms_compatible'],
            'profile': self.__config['gdal']['profile'],
            'nb_processes': self.__config['gdal']['process_count'],
            'zoom': zoom_levels
        }

        tiles_path = '{0}/{1}/{2}'.format(self.tiles_folder_location, discrete_id, version)

        self.log.info("Starting process GDAL2TILES on jobID: {0}, taskID: {1} discreteID: {2}, version: {3} and zoom-levels: {4}"
                            .format(job_id, task_id, discrete_id, version, zoom_levels))
        generate_tiles(self.vrt_file_location(discrete_id), tiles_path, **options)
