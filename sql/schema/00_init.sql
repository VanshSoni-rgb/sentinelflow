-- SentinelFlow PostgreSQL Init
DROP SCHEMA IF EXISTS sentinel CASCADE;
CREATE SCHEMA sentinel;
SET search_path TO sentinel, public;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;
