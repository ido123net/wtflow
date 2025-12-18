-- SQLite3 schema for wtflow database
-- Replaces SQLAlchemy ORM models

CREATE TABLE IF NOT EXISTS workflows (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    lft INTEGER NOT NULL,
    rgt INTEGER NOT NULL,
    workflow_id TEXT NOT NULL,
    FOREIGN KEY (workflow_id) REFERENCES workflows (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_at TIMESTAMP NULL,
    end_at TIMESTAMP NULL,
    retcode INTEGER NULL,
    node_id TEXT NOT NULL,
    FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_nodes_workflow_id ON nodes (workflow_id);
CREATE INDEX IF NOT EXISTS idx_executions_node_id ON executions (node_id);
