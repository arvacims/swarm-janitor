import base64
import logging
from dataclasses import dataclass
from typing import List, Optional

import requests

from swarmjanitor.awsclient import JanitorAwsClient
from swarmjanitor.config import DesiredRole, JanitorConfig
from swarmjanitor.dockerclient import JanitorDockerClient, LoginData, NodeState, SwarmInfo


class JanitorError(RuntimeError):
    message: str

    def __init__(self):
        super().__init__(self.message)


class SwarmManagerError(JanitorError):
    message = 'This node is not a swarm manager.'


class SwarmLeaderError(JanitorError):
    message = 'This node is not a swarm leader.'


class SwarmRoleError(JanitorError):
    message = 'Swarm is active but the desired role does not match.'


@dataclass(frozen=True)
class JoinInfo:
    address: str
    manager: str
    worker: str


@dataclass(frozen=True)
class SystemInfo:
    is_swarm_active: bool
    is_manager: bool
    is_worker: bool
    is_leader: bool
    possible_manager_nodes: List[str]


class JanitorCore:
    config: JanitorConfig
    aws_client: JanitorAwsClient
    docker_client: JanitorDockerClient

    def __init__(self, config: JanitorConfig, aws_client: JanitorAwsClient, docker_client: JanitorDockerClient):
        self.config = config
        self.aws_client = aws_client
        self.docker_client = docker_client

    def _discover_possible_manager_addresses(self) -> List[str]:
        self.aws_client.refresh_session()
        return self.aws_client.discover_possible_manager_addresses(self.config.manager_name_filter)

    def _request_docker_auth(self) -> LoginData:
        self.aws_client.refresh_session()
        ecr_auth_token = self.aws_client.request_auth_token()

        user_and_pass = base64.b64decode(ecr_auth_token).decode('UTF-8').split(':')

        return LoginData(
            username=user_and_pass[0],
            password=user_and_pass[1],
            registry=self.config.registry
        )

    def _is_leader(self, opt_swarm_info: Optional[SwarmInfo] = None) -> bool:
        swarm_info: SwarmInfo = self.docker_client.swarm_info() if opt_swarm_info is None else opt_swarm_info
        return _is_manager(swarm_info) and self.docker_client.node_info(swarm_info.node_id).is_leader

    def prune_system(self):
        self.docker_client.prune_containers()

        if self.config.prune_images:
            self.docker_client.prune_images()

        self.docker_client.prune_networks()

        if self.config.prune_volumes:
            self.docker_client.prune_volumes()

    def refresh_auth(self):
        if not self._is_leader():
            raise SwarmLeaderError
        auth = self._request_docker_auth()
        self.docker_client.refresh_login(auth)
        self.docker_client.update_all_services()

    def refresh_auth_skip(self):
        try:
            self.refresh_auth()
        except JanitorError as error:
            logging.info('Skipped refreshing authentication: %s', error.message)

    def assume_desired_role(self):
        desired_role = self.config.desired_role
        logging.info('Assuming %s role ...', desired_role.value)
        swarm_info = self.docker_client.swarm_info()

        matches_manager = desired_role == DesiredRole.MANAGER and _is_manager(swarm_info)
        matches_worker = desired_role == DesiredRole.WORKER and _is_worker(swarm_info)

        if matches_manager or matches_worker:
            logging.info('No action is required.')
            return

        if _is_swarm_active(swarm_info):
            raise SwarmRoleError

        manager_addresses = self._discover_possible_manager_addresses()
        logging.info('Discovered possible manager nodes: %s', manager_addresses)

        for manager_address in manager_addresses:
            try:
                url = 'http://%s:2380/join' % manager_address
                response = requests.get(url)
                status_code = response.status_code
                logging.info('GET "%s" %s', url, status_code)
                response.raise_for_status()

                join_info = JoinInfo(**response.json())

                join_address = join_info.address
                join_token = join_info.manager if desired_role == DesiredRole.MANAGER else join_info.worker

                logging.info('Joining the swarm via %s using the token "%s" ...', join_address, join_token)
                if not self.docker_client.join_swarm(join_address, join_token):
                    raise RuntimeError('Failed to join the swarm.')

                return
            except:
                logging.warning('Failed to join the swarm via %s.', manager_address, exc_info=True)
                continue

    def join_info(self) -> JoinInfo:
        swarm_info = self.docker_client.swarm_info()

        if not _is_manager(swarm_info):
            raise SwarmManagerError

        node_info = self.docker_client.node_info(swarm_info.node_id)
        join_tokens = self.docker_client.join_tokens()

        return JoinInfo(address=node_info.addr, manager=join_tokens.manager, worker=join_tokens.worker)

    def system_info(self) -> SystemInfo:
        swarm_info = self.docker_client.swarm_info()
        return SystemInfo(
            is_swarm_active=_is_swarm_active(swarm_info),
            is_manager=_is_manager(swarm_info),
            is_worker=_is_worker(swarm_info),
            is_leader=self._is_leader(swarm_info),
            possible_manager_nodes=self._discover_possible_manager_addresses()
        )


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
