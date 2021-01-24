from logger.jsonLogger import Logger
from os import path, makedirs
from src.config import read_json
from osgeo import gdal
from model.enums.storage_provider import StorageProvider

# Read config file
current_dir_path = path.dirname(__file__)
config_path = path.join(current_dir_path, '../config/production.json')
config = read_json(config_path)

# Define logger
log = Logger.get_logger_instance()

def create_folder(folder_path):
    if not path.exists(folder_path):
        log.info("Creating a folder in path: {0}".format(folder_path))
        makedirs(folder_path)


def set_gdal_s3():
    gdal.SetConfigOption('AWS_ACCESS_KEY_ID',
                            config["s3"]["access_key_id"])
    gdal.SetConfigOption('AWS_SECRET_ACCESS_KEY',
                            config["s3"]["secret_access_key"])
    gdal.SetConfigOption(
        'AWS_S3_ENDPOINT', config["s3"]["endpoint_url"])
    gdal.SetConfigOption('AWS_HTTPS', config["s3"]["ssl_enabled"])
    gdal.SetConfigOption('AWS_VIRTUAL_HOSTING',
                            config["s3"]["virtual_hosting"])
    gdal.SetConfigOption('CPL_VSIL_USE_TEMP_FILE_FOR_RANDOM_WRITE', 'YES')

# Initialize tiles location variable
tiles_location_instance = None

def get_tiles_location():
    # This line gets the value of the variable defined outside the function scope
    global tiles_location_instance

    if tiles_location_instance is None:
        storage_provider = config['storage_provider'].upper()

        if (storage_provider == StorageProvider.FS):
           tiles_location_instance = config["fs"]["internal_outputs_path"]

        elif (storage_provider == StorageProvider.S3):
            bucket = config["s3"]["bucket"]
            s3_path = '/vsis3/{0}'.format(bucket)
            tiles_location_instance = s3_path

    return tiles_location_instance
