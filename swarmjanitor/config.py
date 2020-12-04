import os
from dataclasses import dataclass
from enum import Enum, unique


def _str_to_bool(value: str) -> bool:
    return value.lower() in ('true', 'yes', 'y', '1')


@unique
class DesiredRole(Enum):
    MANAGER = 'manager'
    WORKER = 'worker'


@dataclass(frozen=True)
class JanitorConfig:
    availability_zone: str
    registry: str
    desired_role: DesiredRole
    manager_name_filter: str
    interval_assume_role: int
    interval_prune_nodes: int
    interval_prune_system: int
    interval_refresh_auth: int
    prune_images: bool
    prune_volumes: bool

    @classmethod
    def from_env(cls):
        return cls(
            availability_zone=os.getenv('SWARM_NODE_AZ', 'eu-west-1a'),
            registry=os.getenv('SWARM_REGISTRY', '000000000000.dkr.ecr.eu-west-1.amazonaws.com'),
            desired_role=DesiredRole(os.getenv('SWARM_DESIRED_ROLE', 'manager')),
            manager_name_filter=os.getenv('SWARM_MANAGER_NAME_FILTER', 'manager'),
            interval_assume_role=int(os.getenv('SWARM_INTERVAL_ASSUME_ROLE', '45')),
            interval_prune_nodes=int(os.getenv('SWARM_INTERVAL_PRUNE_NODES', '30')),
            interval_prune_system=int(os.getenv('SWARM_INTERVAL_PRUNE_SYSTEM', '86400')),
            interval_refresh_auth=int(os.getenv('SWARM_INTERVAL_REFRESH_AUTH', '3600')),
            prune_images=_str_to_bool(os.getenv('SWARM_PRUNE_IMAGES', 'false')),
            prune_volumes=_str_to_bool(os.getenv('SWARM_PRUNE_VOLUMES', 'false'))
        )
