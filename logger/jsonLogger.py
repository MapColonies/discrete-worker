from MapColoniesJSONLogger.logger import generate_logger
from src.config import Config

config = Config.get_config_instance()
class Logger:
    instance = None

    @staticmethod
    def __get_instance():
        return generate_logger('discrete-worker', log_level=config['logger']['level'],
                               handlers=[{
                                   'type': config['logger']['type'],
                                   'path': config['logger']['path'],
                                   'output': config['logger']['output']
                               }])

    @staticmethod
    def get_logger_instance():
        if Logger.instance is None:
            Logger.instance = Logger.__get_instance()
        return Logger.instance
