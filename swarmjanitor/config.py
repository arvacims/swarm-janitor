import os
from dataclasses import dataclass


def _str_to_bool(value: str) -> bool:
    return value.lower() in ('true', 'yes', 'y', '1')


@dataclass(frozen=True)
class JanitorConfig:
    registry: str = os.environ['SWARM_REGISTRY']
    manager_name_filter: str = os.environ['SWARM_MANAGER_NAME_FILTER']
    interval_prune_system: int = int(os.environ['SWARM_INTERVAL_PRUNE_SYSTEM'])
    interval_refresh_auth: int = int(os.environ['SWARM_INTERVAL_REFRESH_AUTH'])
    prune_images: bool = _str_to_bool(os.environ['SWARM_PRUNE_IMAGES'])
    prune_volumes: bool = _str_to_bool(os.environ['SWARM_PRUNE_VOLUMES'])
