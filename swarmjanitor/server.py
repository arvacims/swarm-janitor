import functools
import logging
from threading import Thread
from typing import Dict

from bottle import Bottle, HTTPError

from swarmjanitor.core import JanitorCore, JanitorError
from swarmjanitor.scheduler import JanitorScheduler
from swarmjanitor.shutdown import Stoppable


def _health() -> Dict:
    return {'status': 'UP'}


def json(error_status: int = 500):
    def json_decorator(request_func):
        @functools.wraps(request_func)
        def wrapper(*args, **kwargs):
            try:
                return vars(request_func(*args, **kwargs))
            except JanitorError as error:
                raise HTTPError(status=error_status, body=error.message)

        return wrapper

    return json_decorator


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
        self.app.get(path='/health', callback=_health)
        self.app.get(path='/jobs', callback=self._jobs)
        self.app.get(path='/join', callback=json(400)(self.core.join_info))
        self.app.get(path='/system', callback=json()(self.core.system_info))

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

    def _jobs(self) -> Dict:
        return {'job_list': self.scheduler.list_jobs()}
