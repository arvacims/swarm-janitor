import logging
from dataclasses import dataclass

import docker
from docker import DockerClient


class JanitorDockerClient:
    @dataclass
    class Authentication:
        username: str
        password: str
        registry: str

    client: DockerClient = docker.from_env()

    def refresh_login(self, auth: Authentication):
        registry = auth.registry

        logging.info('Logging in to the Docker registry "%s" ...', registry)
        login_status = self.client.login(username=auth.username, password=auth.password, registry=registry, reauth=True)
        logging.info('Status: %s', login_status['Status'])

    def update_all_services(self):
        for service in self.client.services.list():
            logging.info('Updating the service "%s" ...', service.name)
            update_status = service.update()
            logging.info('Warnings: %s', update_status['Warnings'])
