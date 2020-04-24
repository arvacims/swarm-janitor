import argparse
import json
import logging
import os
import time

import swarmjanitor.version
from swarmjanitor.awsclient import JanitorAwsClient
from swarmjanitor.config import JanitorConfig
from swarmjanitor.core import JanitorCore
from swarmjanitor.dockerclient import JanitorDockerClient
from swarmjanitor.scheduler import JanitorScheduler
from swarmjanitor.server import JanitorServer
from swarmjanitor.shutdown import ShutdownHandler
from swarmjanitor.utils import SmartEncoder


def run():
    version = swarmjanitor.version.VERSION

    parser = argparse.ArgumentParser(
        prog='swarm-janitor',
        description='Executes maintenance tasks for your Docker Swarm cluster.'
    )
    parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {version}')
    parser.parse_args()

    logging_level = os.getenv('SWARM_LOG_LEVEL', 'INFO')
    logging.basicConfig(format='%(asctime)s %(levelname)-8.8s [%(threadName)10.10s] %(message)s', level=logging_level)

    config = JanitorConfig.from_env()
    config_json = json.dumps(config, indent=2, cls=SmartEncoder)
    logging.info('Starting v%s using the following configuration:\n\n%s\n', version, config_json)

    aws_client = JanitorAwsClient()
    docker_client = JanitorDockerClient()
    core = JanitorCore(config, aws_client, docker_client)
    scheduler = JanitorScheduler(config, core)
    server = JanitorServer.start(core, scheduler)

    shutdown_handler = ShutdownHandler([server, scheduler])

    try:
        time.sleep(5)
        core.assume_desired_role()
    except:
        logging.warning('Failed to assume role.')

    logging.info('Starting scheduler loop ...')
    while not shutdown_handler.stop_now:
        scheduler.run_pending()
        scheduler.tick()

    logging.info('Stopped scheduler loop.')
    logging.shutdown()
