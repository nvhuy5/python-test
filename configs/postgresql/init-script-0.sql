-- Set variables from environment variables (no quotes needed in the \set command)
\set db_name `echo "$POSTGRES_DB"`
\set schema_name `echo "$CELERY_SCHEMA"`

-- Create database (use :'variable' syntax for proper quoting)
-- CREATE DATABASE :"db_name";
\connect :"db_name"

-- Create schema
CREATE SCHEMA :"schema_name";

-- Optional: Create user and grant permissions if needed
\set db_user `echo "$POSTGRES_USER"`
\set db_password `echo "$POSTGRES_PASSWORD"`

-- CREATE USER :"db_user" WITH PASSWORD :'db_password';
GRANT ALL PRIVILEGES ON DATABASE :"db_name" TO :"db_user";
GRANT ALL PRIVILEGES ON SCHEMA :"schema_name" TO :"db_user";
