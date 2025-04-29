from __future__ import annotations

import os
import pathlib
from dataclasses import dataclass
from enum import Enum

DEFAULT_DATABASE_URL = "sqlite:///wtflow.db"


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """Database configuration settings"""

    url: str

    @classmethod
    def from_env(cls) -> DatabaseConfig:
        """Create database config from environment variables"""
        return cls(url=os.environ.get("WTFLOW_DB_URL", DEFAULT_DATABASE_URL))


@dataclass
class StorageConfig:
    """Storage configuration settings"""

    artifacts_dir: pathlib.Path | None = None

    @classmethod
    def from_env(cls) -> StorageConfig:
        """Create storage config from environment variables"""
        artifact_dir_env = os.environ.get("WTFLOW_ARTIFACTS_DIR")
        if not artifact_dir_env:
            return cls()

        artifact_dir = pathlib.Path(artifact_dir_env).resolve()
        artifact_dir.mkdir(parents=True, exist_ok=True)
        config = cls(artifacts_dir=artifact_dir)

        return config


@dataclass
class Config:
    """Global configuration settings"""

    env: Environment
    db: DatabaseConfig
    storage: StorageConfig

    @classmethod
    def load(cls, env: str | None = None) -> Config:
        """Load configuration from environment variables"""
        env_value = env or os.environ.get("WTFLOW_ENV", "development")
        environment = Environment(env_value)

        return cls(
            env=environment,
            db=DatabaseConfig.from_env(),
            storage=StorageConfig.from_env(),
        )
