-- SQLite3 schema for wtflow database
-- Replaces SQLAlchemy ORM models

CREATE TABLE IF NOT EXISTS workflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    lft INTEGER NOT NULL,
    rgt INTEGER NOT NULL,
    workflow_id INTEGER NOT NULL,
    FOREIGN KEY (workflow_id) REFERENCES workflows (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_at TIMESTAMP NULL,
    end_at TIMESTAMP NULL,
    retcode INTEGER NULL,
    node_id INTEGER NOT NULL,
    FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    execution_id INTEGER NOT NULL,
    FOREIGN KEY (execution_id) REFERENCES executions (id) ON DELETE CASCADE
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_nodes_workflow_id ON nodes (workflow_id);
CREATE INDEX IF NOT EXISTS idx_executions_node_id ON executions (node_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_execution_id ON artifacts (execution_id);