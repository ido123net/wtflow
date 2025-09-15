from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import wtflow
from wtflow import db


class DBClient:
    def __init__(self, url: str):
        self.engine = create_engine(url)
        self.Session = sessionmaker(bind=self.engine)
        self.create_all()

    def create_all(self) -> None:
        db.Base.metadata.create_all(self.engine)

    def add_workflow(self, session: Session, workflow: wtflow.Workflow) -> None:
        wf = db.Workflow(name=workflow.name)
        session.add(wf)
        session.flush()
        workflow.set_id(wf.id)
        for node in workflow.nodes:
            self.add_node(session, node, wf.id)
        session.commit()

    def add_node(self, session: Session, node: wtflow.Node, workflow_id: int) -> None:
        n = db.Node(
            name=node.name,
            lft=node._lft,
            rgt=node._rgt,
            workflow_id=workflow_id,
        )
        session.add(n)
        session.flush()
        node.set_id(n.id)
        for artifact in node.artifacts:
            self.add_artifact(session, artifact, n.id)

    def add_artifact(self, session: Session, artifact: wtflow.Artifact, node_id: int) -> None:
        a = db.Artifact(
            name=artifact.name,
            node_id=node_id,
        )
        session.add(a)
        session.flush()

    def start_execution(self, session: Session, node: wtflow.Node) -> None:
        execution = db.Execution(
            start_at=datetime.now(timezone.utc),
            node_id=node.id,
        )
        session.add(execution)
        session.commit()

    def end_execution(self, session: Session, node: wtflow.Node) -> None:
        execution = session.query(db.Execution).filter_by(node_id=node.id).first()
        execution.end_at = datetime.now(timezone.utc)
        execution.retcode = node.retcode
        session.commit()
