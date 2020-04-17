import logging
from dataclasses import dataclass
from enum import Enum, unique
from typing import Dict, List, Optional

import docker
from docker import DockerClient


@dataclass(frozen=True)
class LoginData:
    username: str
    password: str
    registry: str


@dataclass(frozen=True)
class ManagerInfo:
    node_id: str
    addr: str


@unique
class NodeState(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'


@dataclass(frozen=True)
class SwarmInfo:
    local_node_state: NodeState
    node_id: str
    remote_managers: List[ManagerInfo]


@dataclass(frozen=True)
class NodeInfo:
    node_id: str
    status: str
    is_leader: bool


@dataclass(frozen=True)
class JoinTokens:
    manager: str
    worker: str


class JanitorDockerClient:
    client: DockerClient = docker.from_env()

    def node_info(self, node_id: str) -> NodeInfo:
        node_dict = self.client.nodes.get(node_id).attrs
        return NodeInfo(
            node_id=node_dict['ID'],
            status=node_dict['Status']['State'],
            is_leader=node_dict['ManagerStatus']['Leader']
        )

    def swarm_info(self) -> SwarmInfo:
        def remote_managers(manager_dicts: Optional[List[Dict]]) -> List[ManagerInfo]:
            if manager_dicts is None:
                return []
            return [ManagerInfo(manager_dict['NodeID'], manager_dict['Addr']) for manager_dict in manager_dicts]

        swarm_dict: Dict = self.client.info()['Swarm']
        return SwarmInfo(
            local_node_state=NodeState(swarm_dict['LocalNodeState']),
            node_id=swarm_dict['NodeID'],
            remote_managers=remote_managers(swarm_dict['RemoteManagers'])
        )

    def join_tokens(self) -> JoinTokens:
        tokens = self.client.swarm.attrs['JoinTokens']
        return JoinTokens(tokens['Manager'], tokens['Worker'])

    def prune_containers(self):
        logging.info('Pruning containers ...')
        containers = self.client.containers.prune()
        logging.info(containers)

    def prune_images(self):
        logging.info('Pruning images ...')
        images = self.client.images.prune(filters={'dangling': False})
        logging.info(images)

    def prune_networks(self):
        logging.info('Pruning networks ...')
        networks = self.client.networks.prune()
        logging.info(networks)

    def prune_volumes(self):
        logging.info('Pruning volumes ...')
        volumes = self.client.volumes.prune()
        logging.info(volumes)

    def refresh_login(self, auth: LoginData):
        registry = auth.registry

        logging.info('Logging in to the Docker registry "%s" ...', registry)
        login_status = self.client.login(username=auth.username, password=auth.password, registry=registry, reauth=True)
        logging.info('Status: %s', login_status['Status'])

    def update_all_services(self):
        for service in self.client.services.list():
            logging.info('Updating the service "%s" ...', service.name)
            update_status = service.update()
            logging.info('Warnings: %s', update_status['Warnings'])
