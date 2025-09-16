from __future__ import annotations

import os
import pathlib
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    url: str | None = None

    @classmethod
    def from_env(cls) -> DatabaseConfig:
        return cls(url=os.environ.get("WTFLOW_DB_URL"))


@dataclass
class StorageConfig:
    artifacts_dir: pathlib.Path | None = None

    @classmethod
    def from_env(cls) -> StorageConfig:
        artifact_dir_env = os.environ.get("WTFLOW_ARTIFACTS_DIR")
        artifacts_dir = pathlib.Path(artifact_dir_env) if artifact_dir_env else None

        return cls(artifacts_dir=artifacts_dir)


@dataclass
class RunConfig:
    ignore_failure: bool = False

    @classmethod
    def from_env(cls) -> RunConfig:
        ignore_failure_env = os.environ.get("WTFLOW_IGNORE_FAILURE")
        if ignore_failure_env and ignore_failure_env.lower() not in {"0", "1", "true", "false"}:
            raise ValueError("WTFLOW_IGNORE_FAILURE must be one of: 0, 1, true, false")
        else:
            ignore_failure = ignore_failure_env is not None and ignore_failure_env.lower() in {"1", "true"}

        return cls(ignore_failure=ignore_failure)


@dataclass
class Config:
    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    run: RunConfig = field(default_factory=RunConfig)

    @classmethod
    def from_env(cls) -> Config:
        return cls(
            db=DatabaseConfig.from_env(),
            storage=StorageConfig.from_env(),
            run=RunConfig.from_env(),
        )

    @classmethod
    def from_ini(cls, ini_path: str | pathlib.Path) -> Config:
        import configparser

        config = configparser.ConfigParser()
        config.read(ini_path)

        db_url = config.get("database", "url", fallback=None)
        artifacts_dir = config.get("storage", "artifacts_dir", fallback=None)
        ignore_failure = config.getboolean("run", "ignore_failure", fallback=False)

        return cls(
            db=DatabaseConfig(url=db_url),
            storage=StorageConfig(artifacts_dir=pathlib.Path(artifacts_dir) if artifacts_dir else None),
            run=RunConfig(ignore_failure=ignore_failure),
        )
