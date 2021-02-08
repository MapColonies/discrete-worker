import json
from os import path
import constants

def read_json(json_path):
    try:
        if path.exists(json_path):
            with open(json_path, encoding='utf-8') as json_file:
                _json = json.loads(json_file.read())
                return _json
        else:
            raise FileNotFoundError(f"Configure file not found: {json_path}")
    except Exception as e:
        raise e

class Config:
    instance = None

    @staticmethod
    def read_json_2(json_path):
        with open(json_path, encoding='utf-8') as json_file:
            _json = json.loads(json_file.read())
            return _json

    @staticmethod
    def get_config_instance():
        if Config.instance is not None:
            return Config.instance
        else:
            try:
                production_config_path = constants.PRODUCTION_CONFIG_PATH
                default_config_path = constants.DEFAULT_CONFIG_PATH

                if path.exists(production_config_path):
                    Config.instance = Config.read_json_2(production_config_path)
                    print('Using production config file')
                elif path.exists(default_config_path):
                    Config.instance = Config.read_json_2(default_config_path)
                    print('Using default config file')
                else:
                    raise FileNotFoundError("Configure file not found")

                return Config.instance
            except Exception as e:
                raise e
