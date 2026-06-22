from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing, contextmanager
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Generator, Protocol

import wtflow
from wtflow.infra.info import ExecutionInfo, RunInfo
from wtflow.services.db.db_service import DBServiceInterface


class Dataclass(Protocol):
    __dataclass_fields__: ClassVar[dict[str, Any]]


def _digest(node: Dataclass) -> str:
    data = json.dumps(
        asdict(node),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


class Sqlite3DBService(DBServiceInterface):
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        self._run_ids: dict[int, int] = {}
        self._execution_ids: dict[int, int] = {}

        self._create_tables()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection]:
        sqlite3.register_adapter(datetime, self._adapt_datetime)

        with closing(sqlite3.connect(self.database_path)) as cx:
            cx.execute("PRAGMA foreign_keys = ON")
            yield cx

    @staticmethod
    def _adapt_datetime(dt: datetime) -> str:
        return dt.isoformat()

    async def save_graph(self, graph: wtflow.Graph) -> None:
        graph_digest = _digest(graph)

        node_digests = {node: _digest(node) for node in graph.nodes}

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO graphs (digest, name)
                VALUES (?, ?)
                ON CONFLICT(digest) DO NOTHING
                """,
                (graph_digest, graph.name),
            )

            for node, node_digest in node_digests.items():
                conn.execute(
                    """
                    INSERT INTO nodes (
                        digest,
                        name,
                        command,
                        timeout
                    )
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(digest) DO NOTHING
                    """,
                    (
                        node_digest,
                        node.name,
                        node.command,
                        node.timeout,
                    ),
                )

                conn.execute(
                    """
                    INSERT INTO graph_nodes (
                        graph_digest,
                        node_digest
                    )
                    VALUES (?, ?)
                    ON CONFLICT(graph_digest, node_digest) DO NOTHING
                    """,
                    (
                        graph_digest,
                        node_digest,
                    ),
                )

            for from_node, to_node in graph.edges:
                conn.execute(
                    """
                    INSERT INTO graph_edges (
                        graph_digest,
                        from_node_digest,
                        to_node_digest
                    )
                    VALUES (?, ?, ?)
                    ON CONFLICT(
                        graph_digest,
                        from_node_digest,
                        to_node_digest
                    ) DO NOTHING
                    """,
                    (
                        graph_digest,
                        node_digests[from_node],
                        node_digests[to_node],
                    ),
                )

            conn.commit()

    async def update_run_info(self, run_info: RunInfo) -> None:
        graph_digest = _digest(run_info.graph)
        key = id(run_info)

        system_info = run_info.system_info

        with self._get_connection() as conn:
            run_id = self._run_ids.get(key)

            if run_id is None:
                cursor = conn.execute(
                    """
                    INSERT INTO runs (
                        graph_digest,
                        created_at,
                        hostname,
                        os_name,
                        os_release,
                        os_version,
                        machine,
                        cpu_count
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        graph_digest,
                        run_info.created_at,
                        system_info.hostname,
                        system_info.os_name,
                        system_info.os_release,
                        system_info.os_version,
                        system_info.machine,
                        system_info.cpu_count,
                    ),
                )
                lastrowid = cursor.lastrowid
                assert lastrowid
                self._run_ids[key] = lastrowid
            else:
                conn.execute(
                    """
                    UPDATE runs
                    SET
                        start_time = ?,
                        end_time = ?
                    WHERE id = ?
                    """,
                    (
                        run_info.start_time,
                        run_info.end_time,
                        run_id,
                    ),
                )

            conn.commit()

    async def update_execution_info(self, execution_info: ExecutionInfo) -> None:
        graph_digest = _digest(execution_info.graph)
        node_digest = _digest(execution_info.node)
        key = id(execution_info)

        with self._get_connection() as conn:
            execution_id = self._execution_ids.get(key)

            if execution_id is None:
                cursor = conn.execute(
                    """
                    INSERT INTO executions (
                        graph_digest,
                        node_digest,
                        start_time,
                        end_time
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        graph_digest,
                        node_digest,
                        execution_info.start_time,
                        execution_info.end_time,
                    ),
                )
                lastrowid = cursor.lastrowid
                assert lastrowid
                self._execution_ids[key] = lastrowid
            else:
                conn.execute(
                    """
                    UPDATE executions
                    SET
                        start_time = ?,
                        end_time = ?
                    WHERE id = ?
                    """,
                    (
                        execution_info.start_time,
                        execution_info.end_time,
                        execution_id,
                    ),
                )

            conn.commit()

    def _create_tables(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS nodes (
                    digest TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    command TEXT,
                    timeout REAL
                );

                CREATE TABLE IF NOT EXISTS graphs (
                    digest TEXT PRIMARY KEY,
                    name TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS graph_nodes (
                    graph_digest TEXT NOT NULL,
                    node_digest TEXT NOT NULL,

                    PRIMARY KEY (graph_digest, node_digest),

                    FOREIGN KEY (graph_digest)
                        REFERENCES graphs(digest)
                        ON DELETE CASCADE,

                    FOREIGN KEY (node_digest)
                        REFERENCES nodes(digest)
                        ON DELETE RESTRICT
                );

                CREATE TABLE IF NOT EXISTS graph_edges (
                    graph_digest TEXT NOT NULL,
                    from_node_digest TEXT NOT NULL,
                    to_node_digest TEXT NOT NULL,

                    PRIMARY KEY (
                        graph_digest,
                        from_node_digest,
                        to_node_digest
                    ),

                    FOREIGN KEY (graph_digest)
                        REFERENCES graphs(digest)
                        ON DELETE CASCADE,

                    FOREIGN KEY (from_node_digest)
                        REFERENCES nodes(digest)
                        ON DELETE RESTRICT,

                    FOREIGN KEY (to_node_digest)
                        REFERENCES nodes(digest)
                        ON DELETE RESTRICT
                );

                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    graph_digest TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    start_time TEXT,
                    end_time TEXT,

                    hostname TEXT NOT NULL,
                    os_name TEXT NOT NULL,
                    os_release TEXT NOT NULL,
                    os_version TEXT NOT NULL,
                    machine TEXT NOT NULL,
                    cpu_count INTEGER,

                    FOREIGN KEY (graph_digest)
                        REFERENCES graphs(digest)
                        ON DELETE RESTRICT
                );

                CREATE TABLE IF NOT EXISTS executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    graph_digest TEXT NOT NULL,
                    node_digest TEXT NOT NULL,
                    start_time TEXT,
                    end_time TEXT,

                    FOREIGN KEY (graph_digest)
                        REFERENCES graphs(digest)
                        ON DELETE RESTRICT,

                    FOREIGN KEY (node_digest)
                        REFERENCES nodes(digest)
                        ON DELETE RESTRICT
                );
                """
            )
            conn.commit()
