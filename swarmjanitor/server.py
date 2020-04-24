import dataclasses
import functools
import json
import logging
from threading import Thread
from typing import List

import bottle
from bottle import Bottle, HTTPError

from swarmjanitor.core import JanitorCore, JanitorError
from swarmjanitor.scheduler import JanitorScheduler, JobInfo
from swarmjanitor.shutdown import Stoppable
from swarmjanitor.utils import SmartEncoder


def json_response(error_status: int = 500):
    def json_decorator(request_func):
        @functools.wraps(request_func)
        def wrapper(*args, **kwargs):
            try:
                return json.dumps(request_func(*args, **kwargs), cls=SmartEncoder)
            except JanitorError as error:
                raise HTTPError(status=error_status, body=error.message)

        return wrapper

    return json_decorator


@dataclasses.dataclass(frozen=True)
class HealthInfo:
    status: str
    jobs: List[JobInfo]


class JanitorServer(Stoppable):
    app: Bottle
    thread: Thread
    core: JanitorCore
    scheduler: JanitorScheduler

    def __init__(self, core: JanitorCore, scheduler: JanitorScheduler):
        self.app = Bottle()
        self.thread = Thread(target=self._run_server, daemon=True)

        self.core = core
        self.scheduler = scheduler

        self._register_routes()

    def _register_routes(self):
        self.app.get(path='/health', callback=json_response()(self._health))
        self.app.get(path='/system', callback=json_response()(self.core.system_info))
        self.app.get(path='/join', callback=json_response(400)(self.core.join_info))

    def _run_server(self):
        logging.info('Starting server ...')
        self.app.run(host='0.0.0.0', port=2380)

    def _start_daemon(self):
        self.thread.start()

    def stop(self, signum, frame):
        self.app.close()
        logging.info('Stopped server.')

    @classmethod
    def start(cls, core: JanitorCore, scheduler: JanitorScheduler):
        janitor_server = cls(core, scheduler)
        janitor_server._start_daemon()
        return janitor_server

    def _health(self) -> HealthInfo:
        jobs = self.scheduler.list_jobs()

        status_word = 'UP'
        status_code = 200

        if len(jobs) != 4:
            status_word = 'WARN'
            status_code = 500

        bottle.response.status = status_code
        return HealthInfo(
            status=status_word,
            jobs=jobs
        )
