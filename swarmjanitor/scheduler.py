import base64
import functools
import logging
import time
from typing import Any, Dict, List, Optional

from schedule import CancelJob, Job, Scheduler

from swarmjanitor.awsclient import JanitorAwsClient
from swarmjanitor.config import JanitorConfig
from swarmjanitor.dockerclient import JanitorDockerClient
from swarmjanitor.shutdown import Stoppable


def scheduled(catch_exceptions: bool = True, cancel_on_failure: bool = False):
    def scheduled_decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except:
                logging.warning('Job failed.', exc_info=True)

                if not catch_exceptions:
                    raise

                if cancel_on_failure:
                    logging.warning('Job canceled due to failure.')
                    return CancelJob

        return wrapper

    return scheduled_decorator


class JanitorScheduler(Scheduler, Stoppable):
    tick_seconds: int = 1
    config: JanitorConfig
    docker_client: JanitorDockerClient

    def __init__(self, config: JanitorConfig, docker_client: JanitorDockerClient):
        super().__init__()

        self.config = config
        self.docker_client = docker_client

        self._schedule_jobs()

    def _schedule_jobs(self):
        interval_refresh_auth = int(self.config.interval_refresh_auth)
        self.every(interval_refresh_auth).seconds.do(self.update_all_services)

    def stop(self, signum, frame):
        self.clear()
        logging.info('Cleared all jobs.')

    def list_jobs(self) -> List[Dict]:
        return [JanitorScheduler._job_to_dict(job) for job in self.jobs]

    def tick(self):
        time.sleep(self.tick_seconds)

    @staticmethod
    def _job_to_dict(job: Job) -> Dict:
        def _int_or_none(value: Any) -> Optional[int]:
            return None if value is None else int(value)

        def _str_or_none(value: Any) -> Optional[str]:
            return None if value is None else str(value)

        return {
            'name': job.job_func.__name__,
            'interval': _int_or_none(job.interval),
            'latest': _str_or_none(job.latest),
            'unit': _str_or_none(job.unit),
            'atTime': _str_or_none(job.at_time),
            'lastRun': _str_or_none(job.last_run),
            'nextRun': _str_or_none(job.next_run),
            'period': _str_or_none(job.period),
            'startDay': _str_or_none(job.start_day),
        }

    def _request_docker_auth(self) -> JanitorDockerClient.Authentication:
        ecr_auth_token = JanitorAwsClient.request_auth_token()
        user_and_pass = base64.b64decode(ecr_auth_token).decode('UTF-8').split(':')
        return JanitorDockerClient.Authentication(
            username=user_and_pass[0],
            password=user_and_pass[1],
            registry=self.config.registry
        )

    @scheduled()
    def update_all_services(self):
        auth = self._request_docker_auth()
        self.docker_client.refresh_login(auth)
        self.docker_client.update_all_services()
