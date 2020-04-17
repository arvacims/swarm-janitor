import base64

from swarmjanitor.awsclient import JanitorAwsClient
from swarmjanitor.config import JanitorConfig
from swarmjanitor.dockerclient import JanitorDockerClient, JoinTokens, LoginData, SwarmInfo


class JanitorCore:
    config: JanitorConfig
    docker_client: JanitorDockerClient

    def __init__(self, config: JanitorConfig, docker_client: JanitorDockerClient):
        self.config = config
        self.docker_client = docker_client

    def _request_docker_auth(self) -> LoginData:
        ecr_auth_token = JanitorAwsClient.request_auth_token()
        user_and_pass = base64.b64decode(ecr_auth_token).decode('UTF-8').split(':')
        return LoginData(
            username=user_and_pass[0],
            password=user_and_pass[1],
            registry=self.config.registry
        )

    def prune_system(self):
        self.docker_client.prune_containers()

        if self.config.prune_images:
            self.docker_client.prune_images()

        self.docker_client.prune_networks()

        if self.config.prune_volumes:
            self.docker_client.prune_volumes()

    def refresh_auth(self):
        auth = self._request_docker_auth()
        self.docker_client.refresh_login(auth)
        self.docker_client.update_all_services()

    def join_tokens(self) -> JoinTokens:
        if not _is_manager(self.docker_client.swarm_info()):
            raise RuntimeError()
        return self.docker_client.join_tokens()


def _is_swarm_active(swarm_info: SwarmInfo) -> bool:
    return swarm_info.local_node_state == 'active'


def _is_manager(swarm_info: SwarmInfo) -> bool:
    if not _is_swarm_active(swarm_info):
        return False

    node_id_local = swarm_info.node_id
    node_id_managers = [manager.node_id for manager in swarm_info.remote_managers]

    return node_id_local in node_id_managers


def _is_worker(swarm_info: SwarmInfo) -> bool:
    return _is_swarm_active(swarm_info) and not _is_manager(swarm_info)
