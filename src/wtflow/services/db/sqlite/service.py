from __future__ import annotations

import sqlite3
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

import wtflow
from wtflow.infra.executors import Result
from wtflow.services.db.service import DBServiceInterface


class Sqlite3DBService(DBServiceInterface):
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection]:
        sqlite3.register_adapter(datetime, self._adapt_datetime)

        with closing(sqlite3.connect(self.database_path)) as cx:
            yield cx

    @staticmethod
    def _adapt_datetime(dt: datetime) -> str:
        return dt.isoformat()

    def _create_tables(self) -> None:
        schema_path = Path(__file__).parent / "schema.sql"

        with self._get_connection() as conn:
            with open(schema_path, "r") as f:
                schema_sql = f.read()
            conn.executescript(schema_sql)

    def add_workflow(self, workflow: wtflow.Workflow) -> None:
        def add_node(cursor: sqlite3.Cursor, node: wtflow.Node) -> None:
            cursor.execute(
                "INSERT INTO nodes (name, lft, rgt, workflow_id) VALUES (?, ?, ?, ?)",
                (node.name, node.lft, node.rgt, workflow.id),
            )
            row_id = cursor.lastrowid
            assert row_id
            node.id = row_id

            for child in node.children:
                add_node(cursor, child)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO workflows (name, created_at) VALUES (?, ?)",
                (workflow.name, datetime.now(timezone.utc)),
            )
            row_id = cursor.lastrowid
            assert row_id
            workflow.id = row_id

            _node_dict: dict[int, tuple[int, int]] = {}
            add_node(cursor, workflow.root)

            conn.commit()

    def start_execution(self, workflow: wtflow.Workflow, node: wtflow.Node) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO executions (start_at, node_id) VALUES (?, ?)",
                (datetime.now(timezone.utc), node.id),
            )

            conn.commit()

    def end_execution(self, workflow: wtflow.Workflow, node: wtflow.Node, result: Result | None = None) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()

            retcode = result.retcode if result else None

            cursor.execute(
                "UPDATE executions SET end_at = ?, retcode = ?  WHERE node_id = ?",
                (datetime.now(timezone.utc), retcode, node.id),
            )

            conn.commit()
