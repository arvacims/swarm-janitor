import base64
import logging
from dataclasses import dataclass
from typing import List, Optional

import requests

from swarmjanitor.awsclient import JanitorAwsClient
from swarmjanitor.config import DesiredRole, JanitorConfig
from swarmjanitor.dockerclient import JanitorDockerClient, LocalNodeState, LoginData, NodeInfo, NodeState, SwarmInfo


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
    nodes: List[NodeInfo]
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

    def _list_nodes(self) -> List[NodeInfo]:
        swarm_info = self.docker_client.swarm_info()

        if not _is_manager(swarm_info):
            return []

        return self.docker_client.list_nodes()

    def _is_leader(self) -> bool:
        swarm_info = self.docker_client.swarm_info()

        if not _is_manager(swarm_info):
            return False

        return self.docker_client.node_info(swarm_info.node_id).manager_is_leader

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

    def _label_node_az(self, opt_swarm_info: Optional[SwarmInfo] = None):
        swarm_info: SwarmInfo = self.docker_client.swarm_info() if opt_swarm_info is None else opt_swarm_info

        if not _is_swarm_active(swarm_info):
            logging.info('Skipped labeling node.')
            return

        label_key = 'availability_zone'
        label_value = self.config.availability_zone

        logging.info('Assigning label "%s=%s" to this node ...', label_key, label_value)

        self.docker_client.label_node(swarm_info.node_id, label_key, label_value)

    def assume_desired_role(self):
        swarm_info = self.docker_client.swarm_info()
        self._label_node_az(swarm_info)

        desired_role = self.config.desired_role
        logging.info('Assuming %s role ...', desired_role.value)

        local_node_state = swarm_info.local_node_state
        if local_node_state in [LocalNodeState.PENDING, LocalNodeState.ERROR]:
            logging.warning('The local node state is "%s". Leaving swarm ...', local_node_state)
            self.docker_client.leave_swarm()
            self.prune_system()

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
                self.docker_client.join_swarm(join_address, join_token)
                self._label_node_az()
                return
            except:
                logging.warning('Failed to join the swarm via %s.', manager_address, exc_info=True)
                continue

    def prune_nodes(self):
        if not self._is_leader():
            raise SwarmLeaderError

        for node in self._list_nodes():
            node_id = node.node_id

            if node.status == NodeState.READY:
                logging.info('Node %s is ready. No action is required.', node_id)
                continue

            try:
                logging.info('Node %s is NOT ready.', node_id)

                if node.is_manager:
                    logging.info('Demoting manager node %s ...', node_id)
                    self.docker_client.demote_node(node_id)

                logging.info('Removing node %s ...', node_id)
                self.docker_client.remove_node(node_id)
            except:
                logging.warning('Failed to remove the node %s.', node_id, exc_info=True)
                continue

    def prune_nodes_skip(self):
        try:
            self.prune_nodes()
        except JanitorError as error:
            logging.info('Skipped pruning nodes: %s', error.message)

    def join_info(self) -> JoinInfo:
        swarm_info = self.docker_client.swarm_info()

        if not _is_manager(swarm_info):
            raise SwarmManagerError

        node_info = self.docker_client.node_info(swarm_info.node_id)
        join_tokens = self.docker_client.join_tokens()

        return JoinInfo(address=node_info.manager_address, manager=join_tokens.manager, worker=join_tokens.worker)

    def system_info(self) -> SystemInfo:
        swarm_info = self.docker_client.swarm_info()
        return SystemInfo(
            is_swarm_active=_is_swarm_active(swarm_info),
            is_manager=_is_manager(swarm_info),
            is_worker=_is_worker(swarm_info),
            is_leader=self._is_leader(),
            nodes=self._list_nodes(),
            possible_manager_nodes=self._discover_possible_manager_addresses()
        )


def _is_swarm_active(swarm_info: SwarmInfo) -> bool:
    return swarm_info.local_node_state == LocalNodeState.ACTIVE


def _is_manager(swarm_info: SwarmInfo) -> bool:
    if not _is_swarm_active(swarm_info):
        return False

    node_id_local = swarm_info.node_id
    node_id_managers = [manager.node_id for manager in swarm_info.remote_managers]

    return node_id_local in node_id_managers


def _is_worker(swarm_info: SwarmInfo) -> bool:
    return _is_swarm_active(swarm_info) and not _is_manager(swarm_info)
