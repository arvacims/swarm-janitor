import logging
from threading import Thread

from bottle import Bottle

from swarmjanitor.shutdown import Stoppable


class JanitorServer(Stoppable):
    app: Bottle
    thread: Thread

    def __init__(self):
        self.app = Bottle()
        self.thread = Thread(target=self._run_server, daemon=True)

        self._register_routes()

    def _register_routes(self):
        self.app.get(path='/', callback=JanitorServer._health)

    def _run_server(self):
        logging.info('Starting server ...')
        self.app.run(host='localhost', port=2380)

    def _start_daemon(self):
        self.thread.start()

    def stop(self, signum, frame):
        self.app.close()
        logging.info('Closed server.')

    @classmethod
    def start(cls):
        janitor_server = cls()
        janitor_server._start_daemon()
        return janitor_server

    @staticmethod
    def _health():
        return {'status': 'UP'}
