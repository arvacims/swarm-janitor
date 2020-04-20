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
    registry: str = os.environ['SWARM_REGISTRY']
    desired_role: DesiredRole = DesiredRole(os.environ['SWARM_DESIRED_ROLE'])
    manager_name_filter: str = os.environ['SWARM_MANAGER_NAME_FILTER']
    interval_assume_role: int = int(os.environ['SWARM_INTERVAL_ASSUME_ROLE'])
    interval_prune_system: int = int(os.environ['SWARM_INTERVAL_PRUNE_SYSTEM'])
    interval_refresh_auth: int = int(os.environ['SWARM_INTERVAL_REFRESH_AUTH'])
    prune_images: bool = _str_to_bool(os.environ['SWARM_PRUNE_IMAGES'])
    prune_volumes: bool = _str_to_bool(os.environ['SWARM_PRUNE_VOLUMES'])
