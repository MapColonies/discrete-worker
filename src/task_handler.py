from os import path
from kafka import KafkaConsumer, BrokerConnection
from kafka.coordinator.assignors.roundrobin import RoundRobinPartitionAssignor
from logger.jsonLogger import Logger
from src.config import read_json
from src.worker import Worker
import json


class TaskHandler:
    def __init__(self):
        self.log = Logger.get_logger_instance()
        config_path = path.join(path.dirname(__file__), '../config/production.json')
        self.__config = read_json(config_path)
        self.__worker = Worker()

    def handle_tasks(self):
        consumer = KafkaConsumer(bootstrap_servers=self.__config['kafka']['host_ip'],
                                 enable_auto_commit=False,
                                 max_poll_interval_ms=self.__config['kafka']['poll_timeout_milliseconds'],
                                 max_poll_records=self.__config['kafka']['poll_records'],
                                 auto_offset_reset=self.__config['kafka']['offset_reset'],
                                 group_id=self.__config['kafka']['group_id'],
                                 partition_assignment_strategy=[RoundRobinPartitionAssignor])
        try:
            consumer.subscribe([self.__config['kafka']['topic']])
            for task in consumer:
                task_values = json.loads(task.value)
                result = self.execute_task(task_values)
                if result:
                    self.log.info('Finished task with ID: "{0}". Commiting to kafka.'.format(task_values["discrete_id"]))
                    consumer.commit()
                else:
                    # TODO: handle on result != True
                    self.log.error('Execute task failed. ID: "{0}"'.format(task_values["discrete_id"]))
        except Exception as e:
            self.log.error('Error occurred: {0}.'.format(e))
            raise e
        finally:
            consumer.close()

    def execute_task(self, task_values):
        try:
            self.log.info('Executing task {0}'.format(task_values["discrete_id"]))
            self.__worker.buildvrt_utility(task_values)
            self.__worker.gdal2tiles_utility(task_values)
            self.__worker.remove_temp_files()

            return True
        except Exception as e:
            self.log.error('An error occured while processing task id "{0}: {1}"'.format(task_values["discrete_id"], e))
            return False
