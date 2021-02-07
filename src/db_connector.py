from src.config import read_json
from logger.jsonLogger import Logger
from os import path
import requests
import json

current_dir_path = path.dirname(__file__)
config_path = path.join(current_dir_path, '../config/production.json')
config = read_json(config_path)

log = Logger.get_logger_instance()

storage_url = config['discrete_storage']['url']

request_session = requests.Session()
request_session.headers.update({'Content-Type': "application/json", 'Accept': "application/json"})

def update_task(task_id, payload):
    update_url = '{0}/task/{1}'.format(storage_url, task_id)
    log.info('Updating DB with task {0} with data {1}'.format(task_id, str(payload)))
    return request_session.put(url=update_url, data=json.dumps(payload))

def get_task_count(task_id):
    get_url = '{0}/task/{1}'.format(storage_url, task_id)
    log.info('Getting task count for taskId {0}'.format(task_id))
    task = request_session.get(url=get_url).json()
    return task['attempts']

def get_discrete_layer(discrete_id, version):
    get_discrete_by_id_url = '{0}/discrete/{1}/{2}'.format(config["discrete_storage"]["url"], discrete_id, version)
    log.info('Retrieving discrete layer with id {0}'.format(discrete_id))
    return request_session.get(get_discrete_by_id_url).json()
