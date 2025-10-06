from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session, sessionmaker

import wtflow
from wtflow.db.service import DBServiceInterface
from wtflow.storage.service import StorageServiceInterface

from . import models


class OrmDBService(DBServiceInterface):
    def __init__(self, storage_service: StorageServiceInterface, url: str) -> None:
        super().__init__(storage_service)
        self.engine = create_engine(url)
        self.Session = sessionmaker(bind=self.engine)
        self.create_all()

    def create_all(self) -> None:
        models.Base.metadata.create_all(self.engine)

    def add_workflow(self, workflow: wtflow.Workflow) -> None:
        wf = models.Workflow(name=workflow.name)
        with self.Session() as session:
            session.add(wf)
            session.flush()
            workflow._id = wf.id
            for node in workflow.nodes:
                self._add_node(session, node, wf.id)
            session.commit()

    def start_execution(self, workflow: wtflow.Workflow, node: wtflow.Node) -> None:
        execution = models.Execution(
            start_at=datetime.now(timezone.utc),
            node_id=node.id,
        )
        execution.artifacts = [
            models.Artifact(uri=artifact.uri)
            for artifact in node.all_artifacts
            if self.storage_service.get_artifact_uri(artifact, workflow, node) is not None
        ]
        with self.Session() as session:
            session.add(execution)
            session.commit()

    def end_execution(self, workflow: wtflow.Workflow, node: wtflow.Node) -> None:
        with self.Session() as session:
            stmt = (
                update(models.Execution)
                .where(models.Execution.node_id == node.id)
                .values(end_at=datetime.now(timezone.utc))
                .values(retcode=node.result.retcode if node.result else None)
            )
            session.execute(stmt)
            session.commit()

    def _add_node(self, session: Session, node: wtflow.Node, workflow_id: int) -> None:
        n = models.Node(
            name=node.name,
            lft=node._lft,
            rgt=node._rgt,
            workflow_id=workflow_id,
        )
        session.add(n)
        session.flush()
        node._id = n.id
