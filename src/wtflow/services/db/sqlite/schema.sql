-- SQLite3 schema for wtflow database
-- Replaces SQLAlchemy ORM models

CREATE TABLE IF NOT EXISTS workflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    name TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    lft INTEGER NOT NULL,
    rgt INTEGER NOT NULL,
    workflow_id TEXT NOT NULL,
    FOREIGN KEY (workflow_id) REFERENCES workflows (id) ON DELETE CASCADE
) STRICT;

CREATE TABLE IF NOT EXISTS executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_at TEXT NULL,
    end_at TEXT NULL,
    result INTEGER NULL,
    node_id INTEGER NOT NULL,
    FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE
) STRICT;

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_nodes_workflow_id ON nodes (workflow_id);
CREATE INDEX IF NOT EXISTS idx_executions_node_id ON executions (node_id);
