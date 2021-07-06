from logger.jsonLogger import Logger
from src.config import Config
from src.worker import Worker
from model.enums.storage_provider import StorageProvider
import src.utilities as utilities
from pyority_queue.task_handler import *

class Handler:
    def __init__(self):
        self.log = Logger.get_logger_instance()
        self.__config = Config.get_config_instance()
        self.__worker = Worker()
        self.queue_handler = TaskHandler(self.__config["queue"]["job_type"], self.__config["queue"]["task_type"],
                                         self.__config["queue"]["job_manager_url"], self.__config["queue"]["heartbeat_manager_url"],
                                         self.__config["queue"]["heartbeat_interval_seconds"], self.log)

    async def handle_tasks(self):
        try:
            while True:
                task = await self.queue_handler.dequeue(self.__config["queue"]["dequeue_interval_seconds"])
                self.log.info("Task received - {0}".format(task))
                task_id = task["id"]
                job_id = task["jobId"]
                parameters = task["parameters"]
                is_valid, reason = utilities.validate_data(parameters)

                if not is_valid:
                    self.log.error("Validation error - could not process request and could not save status to DB, Committing task with: {0}"
                                   .format(utilities.task_format_log(task)))
                    await self.queue_handler.reject(job_id, task_id, False, reason)
                    continue

                success = await self.do_task_loop(task)

                if success:
                    self.log.info('Committing task with {0}'.format(utilities.task_format_log(task)))
                    await self.queue_handler.ack(job_id, task_id)
        except Exception as e:
            raise e

    async def do_task_loop(self, task):
        parameters = task["parameters"]
        job_id = task["jobId"]
        task_id = task["id"]
        max_retries = self.__config['max_attempts']
        min_zoom_level = parameters["minZoomLevel"]
        max_zoom_level = parameters["maxZoomLevel"]
        zoom_levels = '{0}-{1}'.format(min_zoom_level, max_zoom_level)
        current_retry = task['attempts']
        success = False

        while (current_retry < max_retries and not success):
            current_retry = current_retry + 1
            success, reason = self.execute_task(task, zoom_levels)

            if success:
                self.log.info('Successfully finished {0}'
                              .format(task))
                await self.queue_handler.ack(job_id, task_id)
            else:
                self.log.error('Failed executing task with {0}, current attempt is: {1}'
                               .format(utilities.task_format_log(task), current_retry))
                await self.queue_handler.reject(job_id, task_id, True, reason)
        if current_retry > max_retries and not success:
            await self.queue_handler.reject(job_id, task_id, False)
        return success

    def execute_task(self, task, zoom_levels):
        try:
            self.__worker.buildvrt_utility(task, zoom_levels)
            self.__worker.gdal2tiles_utility(task, zoom_levels)

            if (self.__config['storage_provider'].upper() == StorageProvider.S3):
                self.__worker.remove_s3_temp_files(task, zoom_levels)
            self.__worker.remove_vrt_file(task, zoom_levels)

            success_reason = "Task Completed"
            return True, success_reason
        except Exception as error:
            self.log.error('An error occured while processing {0} with error: {1}'
                           .format(utilities.task_format_log(task), error))
            return False, str(error)
