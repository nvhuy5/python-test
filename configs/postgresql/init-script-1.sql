-- Set variables from environment variables (no quotes needed in the \set command)
\set db_name `echo "$POSTGRES_DB"`
\set schema_name `echo "$CELERY_SCHEMA"`

-- Create database (use :'variable' syntax for proper quoting)
-- CREATE DATABASE :"db_name";
\connect :"db_name"

/* === */
-- Create table in the specified schema
CREATE TABLE IF NOT EXISTS :schema_name.celery_tasks (
    task_id VARCHAR(255) NOT NULL,
    customer_name VARCHAR(255),
    task_name VARCHAR(255),
    task_status VARCHAR(50),
    task_steps JSON,
    PRIMARY KEY (task_id)
);

CREATE TABLE IF NOT EXISTS :schema_name.mapping_rules (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255),
    rules JSON
);
