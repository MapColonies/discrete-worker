from os import path
from kafka import KafkaConsumer, BrokerConnection
from kafka.coordinator.assignors.roundrobin import RoundRobinPartitionAssignor
from logger.jsonLogger import Logger
from src.config import Config
from src.worker import Worker
from model.enums.storage_provider import StorageProvider
from model.enums.status_enum import StatusEnum
import src.db_connector as db_connector
import json
import requests


class TaskHandler:
    def __init__(self):
        self.log = Logger.get_logger_instance()
        self.__config = Config.get_config_instance()
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
            max_retries = self.__config['max_attempts']

            for task in consumer:
                task_values = json.loads(task.value)
                task_id = task_values["task_id"]
                discrete_id =task_values["discrete_id"]
                version = task_values["version"]
                current_retry = db_connector.get_task_count(task_id)
                success = False

                while (current_retry <= max_retries and not success):
                    self.log.info('Processing task ID: {0} with discreteID "{1}", version: {2} and zoom-levels:{3}-{4}'
                                .format(task_id,  discrete_id, version, 
                                task_values["min_zoom_level"], task_values["max_zoom_level"]))

                    update_body = { "status": StatusEnum.in_progress, "attempts": current_retry }
                    db_connector.update_task(task_values['task_id'], update_body)                    
                    success, reason = self.execute_task(task_values)

                    if success:
                        self.log.info('Successfully finished taskID: {0} discreteID: "{1}", version: {2} with zoom-levels:{3}-{4}.'
                                    .format(task_id, discrete_id, version, 
                                            task_values["min_zoom_level"], task_values["max_zoom_level"]))
                        update_body = { "status": StatusEnum.completed, "reason": reason }
                        db_connector.update_task(task_id, update_body)

                    else:
                        self.log.error('Failed executing task with ID {0}, current attempt is: {1}'
                                        .format(task_id, current_retry))        
                        update_body = { "status": StatusEnum.failed, "reason": reason }
                        db_connector.update_task(task_id, update_body)
                        current_retry = current_retry + 1


                self.log.info('Comitting task from kafka with taskId: {0}, discreteID: {1}, version: {2}, zoom-levels: {3}-{4}'
                                    .format(task_id, discrete_id, version,
                                            task_values["min_zoom_level"], task_values["max_zoom_level"]))
                consumer.commit()
        except Exception as e:
            raise e
        finally:
            consumer.close()

    def execute_task(self, task_values):
        discrete_id = task_values["discrete_id"]
        zoom_levels = '{0}-{1}'.format(task_values["min_zoom_level"], task_values["max_zoom_level"])

        try:
            self.__worker.validate_data(task_values)
            self.__worker.buildvrt_utility(task_values)
            self.__worker.gdal2tiles_utility(task_values)

            if (self.__config['storage_provider'].upper() == StorageProvider.S3):
                self.__worker.remove_s3_temp_files(discrete_id, zoom_levels)
            self.__worker.remove_vrt_file(discrete_id, zoom_levels)

            success_reason = "Task Completed"
            return True, success_reason
        except Exception as error:
            self.log.error('An error occured while processing task id "{0}" on zoom-levels {1} with error: {2}'
                           .format(discrete_id, zoom_levels, error))
            return False, str(error)
