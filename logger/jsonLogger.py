from os import path
from jsonlogger.logger import JSONLogger
from MapColoniesJSONLogger.logger import generate_logger
from src.config import read_json

current_dir_path = path.dirname(__file__)
config_path = path.join(current_dir_path, '../config/production.json')
config = read_json(config_path)


class Logger:
    instance = None

    @staticmethod
    def __get_instance():
        return generate_logger('discrete-worker', log_level=config['logger']['level'],
                               handlers=[{
                                   'type': config['logger']['type'],
                                    'path': config['logger']['filename']
                               }])

    @staticmethod
    def get_logger_instance():
        if Logger.instance is None:
            Logger.instance = Logger.__get_instance()
        return Logger.instance
