from kafka import KafkaConsumer, BrokerConnection
from kafka.coordinator.assignors.roundrobin import RoundRobinPartitionAssignor
from logger.jsonLogger import Logger
from src.config import Config
from src.worker import Worker
from model.enums.storage_provider import StorageProvider
from model.enums.status_enum import StatusEnum
import src.request_connector as request_connector
import src.utilities as utilities
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
                                 ssl_context=self.__config['kafka']['ssl_context'],
                                 ssl_cafile=self.__config['kafka']['ssl_cafile'],
                                 ssl_certfile=self.__config['kafka']['ssl_certfile'],
                                 ssl_keyfile=self.__config['kafka']['ssl_keyfile'],
                                 ssl_password=self.__config['kafka']['ssl_password'],
                                 partition_assignment_strategy=[RoundRobinPartitionAssignor])
        try:
            consumer.subscribe([self.__config['kafka']['topic']])

            for task in consumer:
                task_values = json.loads(task.value)
                is_valid, reason = utilities.validate_data(task_values)

                task_id = task_values["task_id"]
                job_id = task_values["job_id"]
                discrete_id = task_values["discrete_id"]
                version = task_values["version"]
                min_zoom_level = task_values["min_zoom_level"]
                max_zoom_level = task_values["max_zoom_level"]
                if not is_valid:
                    if task_id and job_id:
                        update_body = { "status": StatusEnum.failed, "reason": reason }
                        request_connector.update_task(job_id, task_id, update_body)
                        self.log.error("Validation error - could not process request. Comitting from queue")
                    else:
                        self.log.error("Validation error - could not process request and could not save status to DB. Comitting from queue")
                    consumer.commit()
                    continue

                self.do_task_loop(task_id, job_id, discrete_id, version)
                request_connector.post_end_process(discrete_id, version)

                self.log.info('Comitting task from kafka with jobId: {0}, taskId: {1}, discreteID: {2}, version: {3}, zoom-levels: {4}-{5}'
                              .format(job_id, task_id, discrete_id, version, min_zoom_level, max_zoom_level))
                consumer.commit()
        except Exception as e:
            raise e
        finally:
            consumer.close()

    def do_task_loop(self, task_id, job_id, discrete_id, version, min_zoom_level, max_zoom_level):
        max_retries = self.__config['max_attempts']

        current_retry = request_connector.get_task_count(job_id, task_id)
        success = False

        while (current_retry < max_retries and not success):
            current_retry = current_retry + 1
            update_body = { "status": StatusEnum.in_progress, "attempts": current_retry }
            request_connector.update_task(job_id, task_id, update_body)
            success, reason = self.execute_task(discrete_id, min_zoom_level, max_zoom_level)

            if success:
                self.log.info('Successfully finished taskID: {0} discreteID: "{1}", version: {2} with zoom-levels:{3}-{4}.'
                              .format(task_id, discrete_id, version, min_zoom_level, max_zoom_level))
            else:
                self.log.error('Failed executing task with ID {0}, current attempt is: {1}'
                               .format(task_id, current_retry))

            update_body = { "status": StatusEnum.completed if success else StatusEnum.failed, "reason": reason }
            request_connector.update_task(job_id, task_id, update_body)

    def execute_task(self, discrete_id, min_zoom_level, max_zoom_level):
        zoom_levels = '{0}-{1}'.format(min_zoom_level, max_zoom_level)

        try:
            self.__worker.buildvrt_utility(job_id, task_id, discrete_id, version, zoom_levels))
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
