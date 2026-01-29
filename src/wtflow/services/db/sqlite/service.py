from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator

import aiosqlite

import wtflow
from wtflow.services.db.service import DBServiceInterface


class Sqlite3DBService(DBServiceInterface):
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.workflows_id: dict[wtflow.Workflow, int] = {}
        self.nodes_id: dict[wtflow.Node, int] = {}

    def get_workflow_id(self, workflow: wtflow.Workflow) -> int:
        return self.workflows_id[workflow]

    def get_node_id(self, node: wtflow.Node) -> int:
        return self.nodes_id[node]

    @asynccontextmanager
    async def _get_connection(self) -> AsyncGenerator[aiosqlite.Connection]:
        aiosqlite.register_adapter(datetime, self._adapt_datetime)

        async with aiosqlite.connect(self.database_path) as cx:
            yield cx

    @staticmethod
    def _adapt_datetime(dt: datetime) -> str:
        return dt.isoformat()

    async def create_tables(self) -> None:
        schema_path = Path(__file__).parent / "schema.sql"

        async with self._get_connection() as conn:
            with open(schema_path, "r") as f:
                schema_sql = f.read()
            await conn.executescript(schema_sql)

    async def add_workflow(self, workflow: wtflow.Workflow) -> int:
        async def add_node(cursor: aiosqlite.Cursor, node: wtflow.Node, workflow_id: int) -> None:
            await cursor.execute(
                "INSERT INTO nodes (name, command, workflow_id) VALUES (?, ?, ?)",
                (node.name, node.command, workflow_id),
            )
            row_id = cursor.lastrowid
            assert row_id
            self.nodes_id[node] = row_id

            for child in node.children:
                await add_node(cursor, child, workflow_id)

        async with self._get_connection() as conn:
            cursor = await conn.cursor()

            await cursor.execute(
                "INSERT INTO workflows (name, created_at) VALUES (?, ?)",
                (workflow.name, datetime.now(timezone.utc)),
            )
            row_id = cursor.lastrowid
            assert row_id
            workflow_id = row_id
            self.workflows_id[workflow] = row_id

            await add_node(cursor, workflow.root, workflow_id)

            await conn.commit()

        return workflow_id

    async def end_workflow(self, workflow: wtflow.Workflow, result: int) -> None:
        workflow_id = self.workflows_id[workflow]
        async with self._get_connection() as conn:
            cursor = await conn.cursor()

            await cursor.execute(
                "UPDATE workflows SET result = ? WHERE id = ?",
                (result, workflow_id),
            )
            await conn.commit()

    async def start_execution(self, workflow: wtflow.Workflow, node: wtflow.Node) -> None:
        async with self._get_connection() as conn:
            cursor = await conn.cursor()

            await cursor.execute(
                "INSERT INTO executions (start_at, node_id) VALUES (?, ?)",
                (datetime.now(timezone.utc), self.nodes_id[node]),
            )

            await conn.commit()

    async def end_execution(self, workflow: wtflow.Workflow, node: wtflow.Node, result: int | None = None) -> None:
        async with self._get_connection() as conn:
            cursor = await conn.cursor()

            await cursor.execute(
                "UPDATE executions SET end_at = ?, result = ?  WHERE node_id = ?",
                (datetime.now(timezone.utc), result, self.nodes_id[node]),
            )

            await conn.commit()
