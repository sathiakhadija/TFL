-- TfL Intelligence Pipeline — Database Initialisation
-- Idempotent: safe to run multiple times

-- Metabase stores its own application metadata. Keep it separate from the
-- Airflow/TfL database because both apps use tables named "session".
SELECT 'CREATE DATABASE metabase'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'metabase')\gexec

-- ─────────────────────────────────────────────────────────
-- Schemas
-- ─────────────────────────────────────────────────────────

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

-- ─────────────────────────────────────────────────────────
-- raw.line_status
-- Append-only store of TfL line status API responses
-- ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS raw.line_status (
    id                          SERIAL PRIMARY KEY,
    line_id                     TEXT NOT NULL,
    line_name                   TEXT NOT NULL,
    status_severity             INTEGER NOT NULL,
    status_severity_description TEXT,
    reason                      TEXT,
    disruption_category         TEXT,
    disruption_description      TEXT,
    ingested_at                 TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_line_status_line_ingested
    ON raw.line_status (line_id, ingested_at DESC);

CREATE INDEX IF NOT EXISTS idx_line_status_ingested
    ON raw.line_status (ingested_at DESC);

-- ─────────────────────────────────────────────────────────
-- raw.line_arrivals
-- Append-only store of TfL arrival prediction API responses
-- ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS raw.line_arrivals (
    id               SERIAL PRIMARY KEY,
    vehicle_id       TEXT,
    line_id          TEXT NOT NULL,
    line_name        TEXT,
    station_id       TEXT NOT NULL,
    station_name     TEXT NOT NULL,
    platform_name    TEXT,
    destination_id   TEXT,
    destination_name TEXT,
    time_to_station  INTEGER NOT NULL,
    expected_arrival TIMESTAMP WITH TIME ZONE,
    ingested_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_line_arrivals_line_ingested
    ON raw.line_arrivals (line_id, ingested_at DESC);

CREATE INDEX IF NOT EXISTS idx_line_arrivals_station_ingested
    ON raw.line_arrivals (station_id, ingested_at DESC);

-- ─────────────────────────────────────────────────────────
-- raw.station_disruptions
-- Append-only store of TfL station disruption API responses
-- ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS raw.station_disruptions (
    id              SERIAL PRIMARY KEY,
    station_id      TEXT NOT NULL,
    station_name    TEXT NOT NULL,
    disruption_type TEXT,
    category        TEXT,
    description     TEXT,
    additional_info TEXT,
    ingested_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_station_disruptions_station_ingested
    ON raw.station_disruptions (station_id, ingested_at DESC);

CREATE INDEX IF NOT EXISTS idx_station_disruptions_ingested
    ON raw.station_disruptions (ingested_at DESC);
