from logger.jsonLogger import Logger
from src.config import Config
import src.probe as probe
from src.handler import Handler
import constants
from utilities import create_folder, set_gdal_s3
from model.enums.storage_provider import StorageProvider
from pyority_queue.task_handler import *
import asyncio


class Main:
    def __init__(self):
        self.__config = Config.get_config_instance()
        self.__task_handler = Handler()
        self.log = Logger.get_logger_instance()
        self.loop = asyncio.get_event_loop()
        probe.readiness = True
        probe.liveness = True

    def _start_service(self):
        storage_provider = self.__config['storage_provider'].upper()
        try:
            create_folder(constants.VRT_OUTPUT_FOLDER_NAME)

            if (storage_provider == StorageProvider.FS):
                tiles_output_folder = self.__config['fs']['internal_outputs_path']
                create_folder(tiles_output_folder)

            elif (storage_provider == StorageProvider.S3):
                set_gdal_s3()

            self.loop.run_until_complete(self.__task_handler.handle_tasks())
        except Exception as e:
            self.log.error('Error occurred during running service: {0}'.format(e))
            probe.liveness = False


# create thread for app entrypoint
service_thread = threading.Thread(target=Main()._start_service)
service_thread.start()
# start worker probe (liveness & readiness)
probe.start()
