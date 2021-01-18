from logger.jsonLogger import Logger
from os import path, makedirs
from src.config import read_json
from osgeo import gdal

class Utilities:
    def __init__(self):
        self.log = Logger.get_logger_instance()
        config_path = path.join(path.dirname(__file__),
                                '../config/production.json')
        self.__config = read_json(config_path)

    def create_folder(self, folder_path):
        if not path.exists(folder_path):
            self.log.info("Creating a folder in path: {0}".format(folder_path))
            makedirs(folder_path)

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
