import logging
import time

import schedule

from swarmjanitor.server import JanitorServer
from swarmjanitor.shutdown import ShutdownHandler


def run():
    logging.basicConfig(format='%(levelname)s: [%(threadName)10.10s] %(message)s', level='INFO')

    janitor_server = JanitorServer.start()
    shutdown_handler = ShutdownHandler([janitor_server])

    logging.info('Executing scheduler ...')
    while not shutdown_handler.stop_now:
        schedule.run_pending()
        time.sleep(1)

    logging.info('Shutdown completed.')
    logging.shutdown()
