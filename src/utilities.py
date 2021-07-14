from logger.jsonLogger import Logger
from os import path, makedirs
from src.config import Config
from osgeo import gdal
from model.enums.storage_provider import StorageProvider

# Define config file
config = Config.get_config_instance()

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

        if storage_provider == StorageProvider.FS:
            tiles_location_instance = config["fs"]["internal_outputs_path"]

        elif storage_provider == StorageProvider.S3:
            bucket = config["s3"]["bucket"]
            s3_path = '/vsis3/{0}'.format(bucket)
            tiles_location_instance = s3_path

    return tiles_location_instance


def validate_data(task_parameters):
    mandatory_task_fields = config['mandatory_task_fields']
    for field in mandatory_task_fields:
        if field not in task_parameters:
            reason = 'Missing field "{0}"'.format(field)
            return False, reason

    if task_parameters['minZoom'] > task_parameters['maxZoom']:
        reason = 'Minimum zoom level cannot be greater than maximum zoom level'
        return False, reason
    return True, ""


def task_format_log(task):
    parameters = task['parameters']
    if task and parameters:
        log_format = "jobId: {0}, taskId: {1}, discreteID: {2}, version: {3}"\
            .format(task['jobId'], task['id'], parameters['discreteId'], parameters['version'])
        return log_format
