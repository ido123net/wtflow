from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))
    name: Mapped[str] = mapped_column()

    nodes: Mapped[list[Node]] = relationship(back_populates="workflow", cascade="all, delete-orphan")


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    lft: Mapped[int] = mapped_column()
    rgt: Mapped[int] = mapped_column()

    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflows.id"))

    workflow: Mapped[Workflow] = relationship("Workflow", back_populates="nodes")
    executions: Mapped[Execution] = relationship(back_populates="node", cascade="all, delete-orphan")


class Execution(Base):
    __tablename__ = "executions"

    id: Mapped[int] = mapped_column(primary_key=True)
    start_at: Mapped[datetime | None] = mapped_column()
    end_at: Mapped[datetime | None] = mapped_column()
    retcode: Mapped[int | None] = mapped_column()

    node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id"))

    node: Mapped[Node] = relationship("Node", back_populates="executions")
    artifacts: Mapped[list[Artifact]] = relationship(
        "Artifact",
        back_populates="execution",
        cascade="all, delete-orphan",
    )


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    uri: Mapped[str] = mapped_column()

    execution_id: Mapped[int] = mapped_column(ForeignKey("executions.id"))

    execution: Mapped[Execution] = relationship("Execution", back_populates="artifacts")
