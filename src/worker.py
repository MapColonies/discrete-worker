from osgeo import gdal, ogr
from logger.jsonLogger import Logger
from src.config import read_json

class Worker:
    def __init__(self):
        self.log = Logger.get_logger_instance()
