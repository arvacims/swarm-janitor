import argparse
import logging

import swarmjanitor.version
from swarmjanitor.awsclient import JanitorAwsClient
from swarmjanitor.config import JanitorConfig
from swarmjanitor.core import JanitorCore
from swarmjanitor.dockerclient import JanitorDockerClient
from swarmjanitor.scheduler import JanitorScheduler
from swarmjanitor.server import JanitorServer
from swarmjanitor.shutdown import ShutdownHandler


def run():
    parser = argparse.ArgumentParser(
        prog='swarm-janitor',
        description='Executes maintenance tasks for your Docker Swarm cluster.'
    )
    parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {swarmjanitor.version.VERSION}')
    parser.parse_args()

    logging.basicConfig(format='%(levelname)-8.8s [%(threadName)10.10s] %(message)s', level='INFO')

    config = JanitorConfig()
    aws_client = JanitorAwsClient()
    docker_client = JanitorDockerClient()
    core = JanitorCore(config, aws_client, docker_client)
    scheduler = JanitorScheduler(config, core)
    server = JanitorServer.start(core, scheduler)

    shutdown_handler = ShutdownHandler([server, scheduler])

    core.assume_desired_role()

    logging.info('Starting scheduler loop ...')
    while not shutdown_handler.stop_now:
        scheduler.run_pending()
        scheduler.tick()

    logging.info('Stopped scheduler loop.')
    logging.shutdown()
