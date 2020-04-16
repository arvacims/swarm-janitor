import os
from dataclasses import dataclass


@dataclass(frozen=True)
class JanitorConfig:
    registry: str = os.environ['SWARM_REGISTRY']
    interval_refresh_auth: str = os.environ['SWARM_INTERVAL_REFRESH_AUTH']
