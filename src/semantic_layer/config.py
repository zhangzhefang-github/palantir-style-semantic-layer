"""
Configuration objects for semantic layer components.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class OrchestratorConfig:
    db_path: str
    default_engine_type: str = "sqlite"

    @property
    def metadata_db_path(self) -> str:
        return self.db_path

    @property
    def data_db_path(self) -> str:
        return self.db_path
