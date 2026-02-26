from __future__ import annotations

from dataclasses import dataclass

from wtflow.config import Config
from wtflow.services.db.db_service import DBServiceInterface
from wtflow.services.storage.storage_service import StorageServiceInterface


@dataclass
class Servicer:
    db_service: DBServiceInterface
    storage_service: StorageServiceInterface

    @classmethod
    def from_config(cls, config: Config) -> Servicer:
        db_service = config.database.create_db_service()
        storage_service = config.storage.create_storage_service()
        return Servicer(
            db_service=db_service,
            storage_service=storage_service,
        )
