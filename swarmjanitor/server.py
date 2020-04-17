import logging
from threading import Thread
from typing import Dict

from bottle import Bottle

from swarmjanitor.core import JanitorCore
from swarmjanitor.scheduler import JanitorScheduler
from swarmjanitor.shutdown import Stoppable


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
        self.app.get(path='/health', callback=JanitorServer._health)
        self.app.get(path='/jobs', callback=self._jobs)
        self.app.get(path='/join-tokens', callback=self._join_tokens)

    def _run_server(self):
        logging.info('Starting server ...')
        self.app.run(host='localhost', port=2380)

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

    @staticmethod
    def _health() -> Dict:
        return {'status': 'UP'}

    def _jobs(self) -> Dict:
        return {'jobList': self.scheduler.list_jobs()}

    def _join_tokens(self) -> Dict:
        return vars(self.core.join_tokens())
