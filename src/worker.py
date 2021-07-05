from osgeo import gdal
from os import path, remove as remove_file
from logger.jsonLogger import Logger
from config import Config
from gdal2tiles import generate_tiles
from utilities import get_tiles_location
from errors.vrt_errors import VRTError
import constants
import shutil
import src.utilities as utilities


class Worker:
    def __init__(self):
        self.log = Logger.get_logger_instance()
        self.__config = Config.get_config_instance()
        self.tiles_folder_location = get_tiles_location()

    def vrt_file_location(self, discrete_id):
        output_file_name = '{0}.vrt'.format(discrete_id)
        output_path = path.join(constants.VRT_OUTPUT_FOLDER_NAME, output_file_name) 
        return output_path

    def remove_vrt_file(self, job_data):
        vrt_path = self.vrt_file_location(job_data['parameters']['discreteId'])
        self.log.info('Removing vrt file from path "{0}", {1}'.format(vrt_path, utilities.task_format_log(job_data)))
        remove_file(vrt_path)

    def remove_s3_temp_files(self, job_data, zoom_levels):
        tiles_location = '{0}/{1}'.format(self.tiles_folder_location, job_data['parameters']['discreteId'])
        self.log.info('Removing folder {0} on {1}'.format(tiles_location, utilities.task_format_log(job_data)))
        shutil.rmtree(tiles_location)

    def buildvrt_utility(self, job_data, zoom_levels):
        if not (job_data["parameters"]["fileNames"] and job_data["parameters"]["originDirectory"]):
            raise VRTError("jobData didn't have source files data, for {0}"
            .format(utilities.task_format_log(job_data)))

        vrt_config = {
            'VRTNodata': self.__config["gdal"]["vrt"]["no_data"],
            'outputSRS': self.__config["gdal"]["vrt"]["output_srs"],
            'resampleAlg': self.__config["gdal"]["vrt"]["resample_algo"]
        }

        self.log.info("Starting process GDAL-BUILD-VRT on {0} and zoom-levels: {1}"
                        .format(utilities.task_format_log(job_data), zoom_levels))
        mount_path = self.__config['source_mount']
        files = [path.join(mount_path, job_data["parameters"]['originDirectory'], file) for file in job_data["parameters"]['fileNames']]
        vrt_result = gdal.BuildVRT(self.vrt_file_location(job_data["parameters"]['discreteId']), files, **vrt_config)

        if vrt_result != None:
            vrt_result.FlushCache()
            vrt_result = None
        else:
            raise VRTError("Could not create VRT File")


    def gdal2tiles_utility(self, job_data, zoom_levels):
        options = {
            'resampling': self.__config['gdal']['resampling'],
            'tmscompatible': self.__config['gdal']['tms_compatible'],
            'profile': self.__config['gdal']['profile'],
            'nb_processes': self.__config['gdal']['process_count'],
            'zoom': zoom_levels
        }

        tiles_path = '{0}/{1}/{2}'.format(self.tiles_folder_location, job_data['parameters']['discreteId'], job_data['parameters']['version'])

        self.log.info("Starting process GDAL2TILES on {0} and zoom-levels: {1}"
                      .format(utilities.task_format_log(job_data), zoom_levels))
        generate_tiles(self.vrt_file_location(job_data['parameters']['discreteId']), tiles_path, **options)
