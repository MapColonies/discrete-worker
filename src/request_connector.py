from src.config import Config
from logger.jsonLogger import Logger
import requests

log = Logger.get_logger_instance()
config = Config.get_config_instance()

overseer_url = config['overseer']['url']
request_session = requests.Session()
request_session.headers.update({'Content-Type': "application/json", 'Accept': "application/json"})


def post_end_process(job_id, task_id):
    # todo: integrate with new overseer API - pass jobID and taskID
    post_to_overseer_url = '{0}/tasks/{1}/{2}/completed'.format(overseer_url, job_id, task_id)
    log.info('Notifying to overseer that task\'s completed in path {0}'.format(post_to_overseer_url))
    request_session.post(url=post_to_overseer_url)
