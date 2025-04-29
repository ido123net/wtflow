from __future__ import annotations

import os
from typing import Annotated, Generator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

import wtflow
from wtflow.db import DB, Artifact, Node, Workflow

CHECK_INTERVAL = 0.1  # seconds
IDLE_TIMEOUT = 2.0  # seconds

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db() -> DB:
    return DB()


def get_session() -> Generator[Session, None, None]:
    with get_db().Session() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


class TreeNode(BaseModel):
    id: int
    name: str
    children: list[TreeNode] = []
    artifact: list[wtflow.Artifact] = []
    lft: int = Field(exclude=True)
    rgt: int = Field(exclude=True)

    model_config = ConfigDict(use_enum_values=True)


def build_tree(nodes: list[Node]) -> TreeNode | None:
    root = None
    stack: list[TreeNode] = []

    for node in nodes:
        tree_node = TreeNode(
            id=node.id,
            name=node.name,
            children=[],
            artifact=[
                wtflow.Artifact(
                    name=artifact.name,
                    type=artifact.type,
                    file_path=artifact.artifact_path,
                )
                for artifact in node.artifacts
            ],
            lft=node.lft,
            rgt=node.rgt,
        )

        if not stack:
            root = tree_node
        else:
            while stack and stack[-1].rgt < node.lft:
                stack.pop()
            stack[-1].children.append(tree_node)

        stack.append(tree_node)

    return root


@app.get("/api/v1/workflows")
def get_all_workflows(session: SessionDep):
    return session.query(Workflow).order_by(Workflow.id.desc()).limit(20).all()


@app.get("/api/v1/workflow/{workflow_id}/tree")
def get_workflow_tree_id(workflow_id: int, session: SessionDep):
    wf = session.get(Workflow, workflow_id)
    return build_tree(wf.nodes)


@app.get("/api/v1/node/{node_id}/artifacts")
def get_artifact_by_node_id(node_id: int, session: SessionDep):
    return session.query(Artifact).filter(Artifact.node_id == node_id).all()


# @app.get("/api/v1/artifacts/{artifact_id}")
def get_artifact_file_info(artifact_id: int, session: SessionDep):
    """Get metadata about an artifact file."""
    artifact = session.get(Artifact, artifact_id)

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    file_path = artifact.artifact_path

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Artifact file not found")
