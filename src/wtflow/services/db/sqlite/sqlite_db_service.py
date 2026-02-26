from __future__ import annotations

import sqlite3
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

import wtflow
from wtflow.services.db.db_service import DBServiceInterface


class Sqlite3DBService(DBServiceInterface):
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._workflows_id: dict[wtflow.Workflow, int] = {}
        self._nodes_id: dict[wtflow.Node, int] = {}
        self._execution_id: dict[wtflow.Node, int] = {}

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection]:
        sqlite3.register_adapter(datetime, self._adapt_datetime)

        with closing(sqlite3.connect(self.database_path)) as cx:
            yield cx

    @staticmethod
    def _adapt_datetime(dt: datetime) -> str:
        return dt.isoformat()

    async def create_tables(self) -> None:
        schema_path = Path(__file__).parent / "schema.sql"

        with self._get_connection() as conn:
            with open(schema_path, "r") as f:
                schema_sql = f.read()
            conn.executescript(schema_sql)

    async def add_workflow(self, workflow: wtflow.Workflow) -> int:
        async def add_node(cursor: sqlite3.Cursor, node: wtflow.Node, workflow_id: int) -> None:
            async def add_artifact(cursor: sqlite3.Cursor, artifact: wtflow.Artifact, node_id: int) -> None:
                cursor.execute(
                    "INSERT INTO artifacts (name, node_id) VALUES (?, ?)",
                    (artifact.name, node_id),
                )

            cursor.execute(
                "INSERT INTO nodes (name, command, workflow_id) VALUES (?, ?, ?)",
                (node.name, node.command, workflow_id),
            )
            row_id = cursor.lastrowid
            assert row_id
            self._nodes_id[node] = row_id

            for artifact in node.all_artifacts:
                await add_artifact(cursor, artifact, row_id)

            for child in node.children:
                await add_node(cursor, child, workflow_id)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO workflows (name, created_at) VALUES (?, ?)",
                (workflow.name, datetime.now(timezone.utc)),
            )
            row_id = cursor.lastrowid
            assert row_id
            workflow_id = row_id
            self._workflows_id[workflow] = row_id

            await add_node(cursor, workflow.root, workflow_id)

            conn.commit()

        return workflow_id

    async def end_workflow(self, workflow: wtflow.Workflow, result: int) -> None:
        workflow_id = self._workflows_id[workflow]
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE workflows SET result = ? WHERE id = ?",
                (result, workflow_id),
            )
            conn.commit()

    async def start_execution(self, workflow: wtflow.Workflow, node: wtflow.Node) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO executions (start_at, node_id) VALUES (?, ?)",
                (datetime.now(timezone.utc), self._nodes_id[node]),
            )

            conn.commit()

    async def end_execution(self, workflow: wtflow.Workflow, node: wtflow.Node, result: int | None = None) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE executions SET end_at = ?, result = ?  WHERE node_id = ?",
                (datetime.now(timezone.utc), result, self._nodes_id[node]),
            )

            conn.commit()
