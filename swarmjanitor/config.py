import os
from dataclasses import dataclass


@dataclass(frozen=True)
class JanitorConfig:
    registry: str = os.environ['SWARM_REGISTRY']

    interval_prune_system: int = int(os.environ['SWARM_INTERVAL_PRUNE_SYSTEM'])
    interval_refresh_auth: int = int(os.environ['SWARM_INTERVAL_REFRESH_AUTH'])

    _prune_images: str = os.environ['SWARM_PRUNE_IMAGES']
    _prune_volumes: str = os.environ['SWARM_PRUNE_VOLUMES']

    @staticmethod
    def str_to_bool(value: str) -> bool:
        return value.lower() in ('true', 'yes', 'y', '1')

    @property
    def prune_images(self) -> bool:
        return JanitorConfig.str_to_bool(self._prune_images)

    @property
    def prune_volumes(self) -> bool:
        return JanitorConfig.str_to_bool(self._prune_volumes)
