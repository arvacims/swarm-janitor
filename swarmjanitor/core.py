import base64
import logging
from typing import Dict, List

from swarmjanitor.awsclient import JanitorAwsClient
from swarmjanitor.config import JanitorConfig
from swarmjanitor.dockerclient import JanitorDockerClient, JoinTokens, LoginData, NodeState, SwarmInfo


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

    def _is_manager(self) -> bool:
        return _is_manager(self.docker_client.swarm_info())

    def prune_system(self):
        self.docker_client.prune_containers()

        if self.config.prune_images:
            self.docker_client.prune_images()

        self.docker_client.prune_networks()

        if self.config.prune_volumes:
            self.docker_client.prune_volumes()

    def refresh_auth(self):
        # TODO: Only execute this on the leader.
        if not self._is_manager():
            logging.info('This node is not a swarm manager. Aborting ...')
            return

        auth = self._request_docker_auth()
        self.docker_client.refresh_login(auth)
        self.docker_client.update_all_services()

    def join_tokens(self) -> JoinTokens:
        if not self._is_manager():
            raise RuntimeError()
        return self.docker_client.join_tokens()

    def _discover_possible_manager_addresses(self) -> List[str]:
        return JanitorAwsClient.discover_possible_manager_addresses(self.config.manager_name_filter)

    def debug_info(self) -> Dict:
        swarm_info = self.docker_client.swarm_info()
        return {
            'isSwarmActive': _is_swarm_active(swarm_info),
            'isManager': _is_manager(swarm_info),
            'isWorker': _is_worker(swarm_info),
            'possibleManagerNodes': self._discover_possible_manager_addresses()
        }


def _is_swarm_active(swarm_info: SwarmInfo) -> bool:
    return swarm_info.local_node_state == NodeState.ACTIVE


def _is_manager(swarm_info: SwarmInfo) -> bool:
    if not _is_swarm_active(swarm_info):
        return False

    node_id_local = swarm_info.node_id
    node_id_managers = [manager.node_id for manager in swarm_info.remote_managers]

    return node_id_local in node_id_managers


def _is_worker(swarm_info: SwarmInfo) -> bool:
    return _is_swarm_active(swarm_info) and not _is_manager(swarm_info)
