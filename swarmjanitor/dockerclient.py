import logging
from dataclasses import dataclass
from enum import Enum, unique
from typing import Dict, List, Optional

import docker
from docker import DockerClient, auth
from docker.models.nodes import Node
from docker.models.services import Service


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
class LocalNodeState(Enum):
    NONE = ''
    INACTIVE = 'inactive'
    PENDING = 'pending'
    ACTIVE = 'active'
    ERROR = 'error'
    LOCKED = 'locked'


@dataclass(frozen=True)
class SwarmInfo:
    local_node_state: LocalNodeState
    node_id: str
    remote_managers: List[ManagerInfo]


@unique
class NodeState(Enum):
    UNKNOWN = 'unknown'
    DOWN = 'down'
    READY = 'ready'
    DISCONNECTED = 'disconnected'


@dataclass(frozen=True)
class NodeInfo:
    node_id: str
    status: NodeState
    address: str
    is_manager: bool
    manager_address: Optional[str]
    manager_is_leader: Optional[bool]


@dataclass(frozen=True)
class JoinTokens:
    manager: str
    worker: str


class JanitorDockerClient:
    client: DockerClient = docker.from_env()

    def node_info(self, node_id: str) -> NodeInfo:
        return _as_node_info(self.client.nodes.get(node_id).attrs)

    def list_nodes(self) -> List[NodeInfo]:
        return [_as_node_info(node.attrs) for node in self.client.nodes.list()]

    def remove_node(self, node_id: str):
        self.client.api.remove_node(node_id=node_id, force=True)

    def demote_node(self, node_id: str):
        node: Node = self.client.nodes.get(node_id)
        spec: Dict = node.attrs['Spec']

        spec['Role'] = 'worker'

        node.update(node_spec=spec)

    def label_node(self, node_id: str, label_key: str, label_value: str):
        node: Node = self.client.nodes.get(node_id)
        spec: Dict = node.attrs['Spec']

        labels: Dict = spec['Labels']
        labels[label_key] = label_value

        node.update(node_spec=spec)

    def swarm_info(self) -> SwarmInfo:
        def remote_managers(manager_dicts: Optional[List[Dict]]) -> List[ManagerInfo]:
            if manager_dicts is None:
                return []
            return [ManagerInfo(manager_dict['NodeID'], manager_dict['Addr']) for manager_dict in manager_dicts]

        swarm_dict: Dict = self.client.info()['Swarm']
        return SwarmInfo(
            local_node_state=LocalNodeState(swarm_dict['LocalNodeState']),
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

    def refresh_login(self, login_data: LoginData):
        logging.info('Logging in to the Docker registry "%s" ...', login_data.registry)

        login_status = self.client.login(
            username=login_data.username,
            password=login_data.password,
            registry=login_data.registry,
            reauth=True
        )

        logging.info('Status: %s', login_status['Status'])

    # noinspection PyProtectedMember
    def update_service(self, service: Service) -> Dict:
        api_client = self.client.api

        url = api_client._url('/services/{0}/update', service.id)
        params = {'version': service.version}
        headers = {}

        service_spec = service.attrs['Spec']
        container_spec = service_spec['TaskTemplate'].get('ContainerSpec', {})
        image = container_spec.get('Image', None)
        if image is not None:
            registry, repo_name = auth.resolve_repository_name(image)
            auth_header = auth.get_config_header(api_client, registry)
            if auth_header is not None:
                headers['X-Registry-Auth'] = auth_header

        logging.debug('Updating the service: url=%s, data=%s, headers=%s', url, service_spec, headers)
        response = api_client._post_json(url=url, data=service_spec, params=params, headers=headers)
        return api_client._result(response, json=True)

    def update_all_services(self):
        for service in self.client.services.list():
            logging.info('Updating the service "%s" ...', service.name)
            update_status = self.update_service(service)
            logging.info('Warnings: %s', update_status['Warnings'])

    def join_swarm(self, address: str, join_token: str):
        self.client.swarm.join(remote_addrs=[address], join_token=join_token)

    def leave_swarm(self):
        self.client.api.leave_swarm(force=True)


def _as_node_info(node_dict: Dict) -> NodeInfo:
    opt_manager_status: Optional[Dict] = node_dict.get('ManagerStatus', None)

    is_manager = opt_manager_status is not None

    manager_address = opt_manager_status['Addr'] if is_manager else None
    manager_is_leader = opt_manager_status.get('Leader', False) if is_manager else None

    return NodeInfo(
        node_id=node_dict['ID'],
        status=NodeState(node_dict['Status']['State']),
        address=node_dict['Status']['Addr'],
        is_manager=is_manager,
        manager_address=manager_address,
        manager_is_leader=manager_is_leader
    )
