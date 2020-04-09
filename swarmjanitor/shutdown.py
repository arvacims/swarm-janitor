import logging
import signal
from typing import List


class Stoppable:

    def stop(self, signum, frame):
        pass


class ShutdownHandler(Stoppable):
    components: List[Stoppable]

    stop_now: bool = False

    def __init__(self, components: List[Stoppable]):
        self.components = components

        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def stop(self, signum, frame):
        logging.info('Shutting down ...')

        for component in self.components:
            component.stop(signum, frame)

        self.stop_now = True
