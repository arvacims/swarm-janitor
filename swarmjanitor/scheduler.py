import functools
import logging
import time
from typing import Any, Dict, List, Optional

from schedule import CancelJob, Job, Scheduler

from swarmjanitor.config import JanitorConfig
from swarmjanitor.core import JanitorCore
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


class JanitorScheduler(Scheduler, Stoppable):
    tick_seconds: int = 1
    config: JanitorConfig
    core: JanitorCore

    def __init__(self, config: JanitorConfig, core: JanitorCore):
        super().__init__()

        self.config = config
        self.core = core

        self._schedule_jobs()

    def _schedule_jobs(self):
        self.every(self.config.interval_assume_role).seconds.do(scheduled()(self.core.assume_desired_role))
        self.every(self.config.interval_prune_nodes).seconds.do(scheduled()(self.core.prune_nodes))
        self.every(self.config.interval_prune_system).seconds.do(scheduled()(self.core.prune_system))
        self.every(self.config.interval_refresh_auth).seconds.do(scheduled()(self.core.refresh_auth_skip))

    def stop(self, signum, frame):
        self.clear()
        logging.info('Cleared all jobs.')

    def list_jobs(self) -> List[Dict]:
        return [_job_to_dict(job) for job in self.jobs]

    def tick(self):
        time.sleep(self.tick_seconds)
