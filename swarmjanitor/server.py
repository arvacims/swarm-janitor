import logging
from threading import Thread
from typing import Dict

from bottle import Bottle

from swarmjanitor.scheduler import JanitorScheduler
from swarmjanitor.shutdown import Stoppable


class JanitorServer(Stoppable):
    app: Bottle
    thread: Thread
    scheduler: JanitorScheduler

    def __init__(self, scheduler: JanitorScheduler):
        self.app = Bottle()
        self.thread = Thread(target=self._run_server, daemon=True)
        self.scheduler = scheduler

        self._register_routes()

    def _register_routes(self):
        self.app.get(path='/health', callback=JanitorServer._health)
        self.app.get(path='/jobs', callback=self._jobs)

    def _run_server(self):
        logging.info('Starting server ...')
        self.app.run(host='localhost', port=2380)

    def _start_daemon(self):
        self.thread.start()

    def stop(self, signum, frame):
        self.app.close()
        logging.info('Stopped server.')

    @classmethod
    def start(cls, scheduler: JanitorScheduler):
        janitor_server = cls(scheduler)
        janitor_server._start_daemon()
        return janitor_server

    @staticmethod
    def _health() -> Dict:
        return {'status': 'UP'}

    def _jobs(self) -> Dict:
        return {'jobList': self.scheduler.list_jobs()}
