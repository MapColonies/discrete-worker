from os import path
from kafka import KafkaConsumer, BrokerConnection
from kafka.coordinator.assignors.roundrobin import RoundRobinPartitionAssignor
from logger.jsonLogger import Logger
from src.config import read_json
import json


class TaskHandler:
    def __init__(self):
        self.log = Logger.get_logger_instance()

        current_dir_path = path.dirname(__file__)
        config_path = path.join(current_dir_path, '../config/production.json')
        self.__config = read_json(config_path)

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
                    self.log.info(f'Finished task - commitng to kafka')
                    consumer.commit()
        except Exception as e:
            self.log.error(f'Error occurred: {e}.')
            raise e
        finally:
            consumer.close()

    def execute_task(self, task_values):
        try:
            self.log.info(f'Executing task')
            // TODO: add task id for all logs of specific task including when commiting it to kafka
            // TODO: gdal2tiles will be added here
            return True
        except Exception as e:
            self.log.error(f'Error occurred while exporting: {e}.')
            return False
