from __future__ import annotations

import logging

from sqlalchemy import ForeignKey, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

from wtflow.nodes import Node
from wtflow.workflow import Workflow

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class WorkflowDB(Base):
    __tablename__ = "workflow"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)

    nodes: Mapped[list[NodeDB]] = relationship(back_populates="workflow", cascade="all, delete-orphan")


class NodeDB(Base):
    __tablename__ = "node"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflow.id", ondelete="CASCADE"), nullable=False)
    lft: Mapped[int] = mapped_column(nullable=False)
    rgt: Mapped[int] = mapped_column(nullable=False)
    retcode: Mapped[int] = mapped_column(nullable=True)

    workflow: Mapped[WorkflowDB] = relationship(back_populates="nodes")
    artifacts: Mapped[list[ArtifactDB]] = relationship(back_populates="node", cascade="all, delete-orphan")


class ArtifactDB(Base):
    __tablename__ = "artifact"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    path: Mapped[str] = mapped_column(nullable=False)
    type: Mapped[str] = mapped_column(nullable=False)
    node_id: Mapped[int] = mapped_column(ForeignKey("node.id", ondelete="CASCADE"), nullable=False)

    node: Mapped[NodeDB] = relationship(back_populates="artifacts")


class DB:
    def __init__(self, db_url: str = "sqlite:///wtflow.db") -> None:
        self.engine = create_engine(db_url, echo=False, future=True)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.create_tables()

    def create_tables(self) -> None:
        Base.metadata.create_all(self.engine)

    def insert_workflow(self, workflow: Workflow) -> None:
        with self.Session() as session:
            wf = WorkflowDB(name=workflow.name)
            session.add(wf)
            session.flush()
            workflow._id = wf.id
            self._add_node(session, workflow.root, wf)
            session.commit()

    def update_node(self, node: Node) -> None:
        with self.Session() as session:
            nd = session.get(NodeDB, node._id)
            assert nd is not None
            nd.retcode = node.retcode
            session.commit()

    def _add_node(self, session: Session, node: Node, workflow: WorkflowDB) -> None:
        nd = NodeDB(name=node.name, lft=node._lft, rgt=node._rgt, workflow=workflow)
        session.add(nd)
        session.flush()
        node._id = nd.id
        for child in node.children:
            self._add_node(session, child, workflow)

    def add_artifacts(self, node: Node) -> None:
        with self.Session() as session:
            for artifact in node.artifacts:
                artifact_db = ArtifactDB(path=str(artifact.path), type=artifact.type.value, node_id=node._id)
                session.add(artifact_db)
            session.commit()
