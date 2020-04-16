import logging

from swarmjanitor.config import JanitorConfig
from swarmjanitor.dockerclient import JanitorDockerClient
from swarmjanitor.scheduler import JanitorScheduler
from swarmjanitor.server import JanitorServer
from swarmjanitor.shutdown import ShutdownHandler


def run():
    logging.basicConfig(format='%(levelname)-8.8s [%(threadName)10.10s] %(message)s', level='INFO')

    config = JanitorConfig()
    docker_client = JanitorDockerClient()
    scheduler = JanitorScheduler(config, docker_client)
    server = JanitorServer.start(scheduler)

    shutdown_handler = ShutdownHandler([server, scheduler])

    scheduler.run_all(delay_seconds=5)

    logging.info('Starting scheduler loop ...')
    while not shutdown_handler.stop_now:
        scheduler.run_pending()
        scheduler.tick()

    logging.info('Stopped scheduler loop.')
    logging.shutdown()
