from os import path
from src.worker import Worker
from logger.jsonLogger import Logger
from src.config import read_json
import src.probe as probe
from src.task_handler import TaskHandler
import threading
import worker_constants
from utilities import Utilities
from model.enums.storage_provider import StorageProvider


class Main:
    def __init__(self):
        current_dir_path = path.dirname(__file__)
        config_path = path.join(current_dir_path, '../config/production.json')
        self.__config = read_json(config_path)
        self.__task_handler = TaskHandler()
        self.__utilities = Utilities()

        self.log = Logger.get_logger_instance()
        probe.readiness = True
        probe.liveness = True

    def _start_service(self):
        self.log.info('Service is listening to broker: {0}, topic: {1}'.format(self.__config["kafka"]["host_ip"], self.__config["kafka"]["topic"]))
        try:
            self.__utilities.create_folder(worker_constants.VRT_OUTPUT_FOLDER_NAME)
            self.__utilities.create_folder(worker_constants.TILES_OUTPUT_FOLDER_NAME)

            if (self.__config['storage_provider'].upper() == StorageProvider.S3):
                self.__utilities.set_gdal_s3()

            self.__task_handler.handle_tasks()
        except Exception as e:
            self.log.error('Error occurred during running service: {0}'.format(e))
            probe.liveness = False


service_thread = threading.Thread(target=Main()._start_service)
service_thread.start()
probe.start()
