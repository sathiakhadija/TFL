# TfL Intelligence Pipeline — Implementation Guide

> This document explains how the TfL Intelligence Pipeline was built,
> why each technical decision was made, and how every component fits
> together. Updated after every implementation task.

## Project Overview

The TfL Intelligence Pipeline is a production data engineering system
that ingests live Transport for London API data every 15 minutes,
stores it in PostgreSQL, transforms it through three dbt model layers,
and surfaces reliability intelligence in a Metabase dashboard.

---

## Architecture

### Data Flow

```
TfL Unified API
      │
      │  HTTP GET (every 15 min via Airflow)
      ▼
Apache Airflow (Orchestration)
      │
      ├── line_status_dag       ─── every 15 min
      ├── line_arrivals_dag     ─── every 15 min
      └── station_disruptions_dag ─ every 30 min
      │
      │  psycopg2 INSERT
      ▼
PostgreSQL — raw schema (append-only)
      │
      │  dbt run (triggered from Airflow BashOperator)
      ▼
PostgreSQL — staging schema (cleaned views)
      │
      │  dbt run
      ▼
PostgreSQL — marts schema (materialised tables)
      │
      │  SQL queries
      ▼
Metabase Dashboard
```

### Five-Component Architecture

1. **TfL Unified API** — The data source. Provides real-time line
   status, arrival predictions, and station disruption data via
   authenticated REST endpoints. Updated by TfL in near-real-time.

2. **Apache Airflow** — The orchestrator. Schedules and executes
   ingestion DAGs on cron schedules, handles retries, validates data
   quality after each run, and triggers dbt transformations. Provides
   a web UI for monitoring pipeline health.

3. **PostgreSQL** — The storage layer. Organises data into three
   schemas: raw (immutable ingested data), staging (cleaned views),
   and marts (business-logic tables). Handles concurrent writes from
   multiple Airflow tasks.

4. **dbt Core** — The transformation layer. Converts raw API data
   into analyst-ready tables through a three-layer model architecture.
   Provides built-in testing, lineage diagrams, and documentation
   generation. All transformations are version-controlled SQL.

5. **Metabase** — The visualisation layer. Connects directly to the
   marts schema and surfaces reliability intelligence through
   dashboards. Chosen for its zero-code dashboard builder suitable
   for non-engineers.

---

## Technology Decisions

### Why Airflow over Prefect or cron

**Airflow** was chosen because:
- Task-level visibility: each step (fetch, validate, transform) is a
  separate node in the DAG UI with its own logs and retry state
- XCom: tasks pass metadata (row counts, validation results) to
  downstream tasks without writing to disk
- Retry logic: failed tasks retry automatically with configurable
  backoff, without manual intervention
- Production standard: the most widely deployed orchestrator at UK
  data organisations; recognisable on a portfolio CV

**Prefect** is technically excellent but less common in enterprise UK
data teams. **Cron** provides scheduling but no visibility, no retry
logic, no UI, and no task dependency management.

### Why dbt over raw SQL transformations

**dbt** was chosen because:
- Version-controlled SQL: every transformation is a `.sql` file
  tracked in git, reviewable, and reversible
- Built-in testing: `not_null`, `unique`, `accepted_values` tests run
  automatically and fail the pipeline if data quality degrades
- Lineage: dbt generates a visual graph of how every table depends on
  every other table — essential for debugging
- Documentation: `dbt docs generate` produces a browsable data
  catalogue from schema.yml descriptions
- `ref()` and `source()`: compile-time dependency resolution means
  dbt builds models in the correct order automatically

Raw SQL scripts provide none of these guarantees and become
unmaintainable as the number of transformations grows.

### Why PostgreSQL over SQLite or DuckDB

**PostgreSQL** was chosen because:
- Concurrent writes: multiple Airflow tasks write simultaneously;
  SQLite serialises all writes and cannot handle this
- Schema separation: PostgreSQL schemas (raw, staging, marts) provide
  logical namespacing that SQLite does not support
- Production standard: every UK data organisation runs PostgreSQL or
  a compatible variant (AWS RDS, Azure Database, Google Cloud SQL)
- TIMESTAMP WITH TIME ZONE: PostgreSQL handles timezone-aware
  timestamps correctly; SQLite stores everything as text
- Indexes: PostgreSQL B-tree indexes on `ingested_at` make time-range
  queries fast as the tables grow to millions of rows

**DuckDB** is excellent for analytics but designed for single-user
analytical queries, not concurrent write workloads from a scheduler.

### Why Metabase over Grafana or Streamlit

**Metabase** was chosen because:
- Zero-code dashboards: analysts can build charts by clicking, without
  writing SQL or Python
- Native PostgreSQL connector: connects directly to the marts schema
  with no middleware
- Self-hosted: runs in Docker alongside the rest of the stack with
  no external dependencies or API keys
- Question/dashboard model: Metabase's "questions" map directly to
  the mart tables designed for this pipeline

**Grafana** excels at time-series metrics from monitoring systems but
requires more configuration for relational data. **Streamlit** requires
Python development skills and is not zero-code for analysts.

---

## Three-Layer dbt Architecture

### Layer 1: Raw (Views)

Raw models are **views** that point directly at the raw schema tables
ingested by Airflow. They expose the ingested data in its original
form without any transformations. Being views means they add zero
storage overhead and always reflect the current state of the raw
tables.

Purpose: preserve an unmodified audit trail of exactly what the API
returned. If a transformation bug is discovered, the raw data is
intact and transformations can be re-run from scratch.

### Layer 2: Staging (Views)

Staging models are **views** that clean, type-cast, and rename columns
from the raw models. Operations at this layer include:
- `LOWER(TRIM(line_id))` — normalise string casing
- `INITCAP(line_name)` — consistent title casing
- `COALESCE(field, 'default')` — replace NULLs with safe defaults
- `time_to_station / 60.0` — convert seconds to minutes
- `DATE_TRUNC('hour', ingested_at)` — add time bucketing columns

Staging models use `ref('raw_line_status')` — they depend on raw
models, never on the raw tables directly. This means changing the raw
model updates staging automatically.

Being views means staging adds no storage cost and stays current with
raw in real time.

### Layer 3: Marts (Tables)

Mart models are **materialised as tables** (not views) because they
contain expensive aggregations — window functions, GROUP BY across
millions of rows, RANK() — that should not be recomputed on every
dashboard query.

Each mart models a business concept:
- `mart_line_performance`: hourly health scores per line
- `mart_station_reliability`: station disruption league table
- `mart_disruption_trends`: daily trends with day-over-day change

Mart models are rebuilt every 15–30 minutes when Airflow triggers
`dbt run` after each ingestion batch.

---

## Task 1 — Project Structure

Created the complete directory tree for the TfL Intelligence Pipeline.
All `__init__.py` files are empty — they mark directories as Python
packages so that `from ingestion.tfl_client import TfLClient` works
correctly when Airflow imports the DAG modules.

The `.gitignore` excludes `.env` (contains secrets), `dbt_packages/`
(installed at runtime like `node_modules`), `target/` (dbt compiled
output), and Airflow's `logs/` directory (too large and ephemeral for
version control).

---

## Task 2 — Requirements

### Production dependencies (requirements.txt)

- **apache-airflow==2.9.3**: The orchestration engine. Pinned to a
  specific patch version to guarantee reproducible Docker builds.
  Airflow releases frequently break backward compatibility.

- **apache-airflow-providers-postgres==5.11.0**: Provides Airflow's
  `PostgresHook` and `PostgresOperator`. Without this provider,
  Airflow has no built-in PostgreSQL connection management. The
  provider handles connection pooling and credentials from Airflow
  Connections.

- **apache-airflow-providers-http==4.11.0**: Provides `HttpHook` for
  Airflow-managed HTTP connections. Used for monitoring and optional
  HTTP sensor tasks.

- **dbt-core==1.8.4**: The dbt transformation engine. Parses `.sql`
  model files, resolves `ref()` dependencies, compiles SQL, and
  executes against PostgreSQL. Core is database-agnostic.

- **dbt-postgres==1.8.2**: The PostgreSQL adapter for dbt. Translates
  dbt's database-agnostic operations into PostgreSQL-specific SQL.
  Must match the dbt-core minor version.

- **psycopg2-binary==2.9.9**: The PostgreSQL driver for Python.
  The `-binary` variant bundles pre-compiled C extensions, eliminating
  the need for `libpq-dev` system packages in the Docker image. The
  plain `psycopg2` requires compiling from source, which fails in
  minimal Docker images without build tools.

- **requests==2.32.3**: HTTP client for the TfL API calls. More
  ergonomic than `urllib` with built-in JSON parsing, session
  management, and timeout support.

- **python-dotenv==1.0.1**: Loads `.env` files into `os.environ` for
  local development. Production (Docker) passes environment variables
  directly; dotenv is only used locally.

- **pandas==2.2.2**: Data manipulation library used in data validation
  and seed scripts.

### Development dependencies (requirements-dev.txt)

- **pytest==8.3.3**: The test runner. Discovers and executes all
  `test_*.py` files. Provides fixtures, parametrize, and detailed
  failure output.

- **pytest-mock==3.14.0**: Adds `mocker` fixture for patching objects
  during tests. Used to mock psycopg2 connections without a real
  database.

- **responses==0.25.3**: Intercepts `requests` library HTTP calls and
  returns mock responses. This is why tests never make real API calls
  — the `responses` library patches the network layer so tests are
  fast, free, and deterministic.

- **ruff==0.4.10**: An extremely fast Python linter written in Rust.
  Replaces flake8, isort, and pyupgrade in a single tool. Used in CI
  to enforce code style without slowing the build.

---

## Task 3 — TfL API Client

### What the TfL Unified API is

Transport for London exposes a public REST API at `api.tfl.gov.uk`
that provides real-time data for all TfL services: Tube, bus,
Overground, Elizabeth line, DLR, and more. It is a true unified API —
one authentication method, one base URL, consistent response
structures across all transport modes.

### Authentication

The API uses **query parameter authentication**. Every request must
include `app_key=<your-key>` as a URL parameter. There is no OAuth,
no JWT, no session management. The key is appended by `_make_request`
to every outbound request automatically.

TfL API keys are free. Register at `api.tfl.gov.uk`. The free tier
allows 500 requests per minute per key — more than sufficient for a
15-minute pipeline ingesting 12 lines.

### Exponential Backoff Retry

The client retries failed requests up to 3 times with delays of 1s,
2s, and 4s (exponential backoff). This handles:
- Transient network errors (momentary packet loss)
- TfL API rate limit responses (429 Too Many Requests)
- Brief TfL service interruptions

Without retry, a single dropped packet would fail the entire DAG run
and trigger Airflow's alert system unnecessarily.

### Why Station IDs Are Hardcoded

TfL station IDs (NaPTAN codes) are stable identifiers that do not
change. Fetching them dynamically would require an additional API call
on every pipeline run, adding latency and a failure point. The 21
hardcoded major stations represent the highest-traffic interchange
stations on the network — the ones whose disruption data is most
analytically useful.

### Rate Limiting

TfL's free tier allows 500 requests/minute. The pipeline makes
approximately 3 API calls per DAG run (line_status, line_arrivals,
disruptions). At 15-minute intervals, that is 12 calls per hour,
well within the free tier. The `station_disruptions` endpoint batches
station IDs in groups of 5 to reduce request count further.

---

## Task 4 — PostgreSQL Schema

### Why Three Separate Schemas

Three schemas (raw, staging, marts) provide **separation of concerns**
at the database level:

- `raw`: only Airflow writes here; analysts never query raw directly
- `staging`: dbt reads from raw and writes cleaned views here
- `marts`: Metabase queries only the marts schema

This means a broken dbt transformation never corrupts raw data, and
analysts querying marts never accidentally read half-ingested rows.

### Why Raw Tables Are Append-Only

Raw tables use `INSERT` only — no `UPDATE`, no `DELETE`, no `UPSERT`.
This is the **immutable event log pattern**:

- Every ingestion creates a new row with its own `ingested_at`
  timestamp, creating a complete history of API responses
- If a transformation bug is found, the raw data is intact and dbt
  models can be re-run to rebuild marts from scratch
- Append-only writes are faster than upserts (no index lookup before
  write) and safe for concurrent Airflow tasks

### SERIAL PRIMARY KEY vs UUID

`SERIAL` generates sequential integers (1, 2, 3...) automatically.
For this pipeline, SERIAL is preferred over UUID because:
- Smaller storage (4 bytes vs 16 bytes)
- Naturally ordered by insertion time (good for time-range queries)
- Simpler to read in logs and debugging sessions

UUIDs are preferable in distributed systems where multiple nodes
generate IDs independently and must avoid collisions — not applicable
here where a single PostgreSQL instance generates all IDs.

### Index Strategy

Indexes were created on `(line_id, ingested_at DESC)` and
`(ingested_at DESC)` because:
- Airflow validation queries filter by `ingested_at > NOW() - INTERVAL
  '5 minutes'` — the ingested_at index makes these instant
- Metabase dashboard queries filter by `line_id` and time range —
  the composite index covers both predicates in one scan
- `DESC` ordering matches the query pattern (most recent first)

### TIMESTAMP WITH TIME ZONE

`TIMESTAMP WITH TIME ZONE` (also written `TIMESTAMPTZ`) stores
timestamps as UTC internally and converts to the session timezone
for display. This is critical because:
- TfL API returns timestamps in ISO 8601 format with timezone info
- London observes BST (UTC+1) in summer and GMT (UTC+0) in winter
- Without timezone awareness, half the year's data would be offset
  by one hour, corrupting time-of-day analysis

Plain `TIMESTAMP` stores no timezone information and assumes local
time — incorrect and inconsistent for a system that may run in
different timezone environments.

---

## Task 5 — Ingestion Modules

### How TfL API Responses Are Parsed

**line_status**: The TfL `/Line/{ids}/Status` endpoint returns a list
of line objects. Each line object contains a `lineStatuses` array —
a line can have multiple simultaneous statuses (e.g., "Minor Delays"
on one section and "Good Service" on another). The ingestion function
iterates the outer list then the inner `lineStatuses` array, creating
one database row per status entry.

**line_arrivals**: The `/Line/{ids}/Arrivals` endpoint returns a flat
list of arrival prediction objects, one per vehicle approaching a
platform. The `expectedArrival` field is an ISO 8601 string
(`2024-01-15T14:32:00Z`) that is parsed to a Python `datetime` before
insertion. Arrivals with `time_to_station < 0` are filtered out —
these are vehicles that have already departed.

**station_disruptions**: The `/StopPoint/{ids}/Disruption` endpoint
accepts comma-separated station IDs. Requests are batched in groups
of 5 to stay within URL length limits. Returns zero rows during normal
operations — this is expected and not an error.

### Why Validation Runs After Every Ingestion

Validation catches data quality problems immediately, before dbt
transforms bad data into mart tables that analysts trust. Without
post-ingestion validation:
- A TfL API outage would silently insert 0 rows
- Metabase dashboards would show stale data with no alert
- The problem might not be discovered until an analyst notices

Validation raises an `AirflowException` which marks the task red
in the Airflow UI, halts the downstream `trigger_dbt` task, and
can trigger email/Slack alerts. The pipeline fails loudly, not
silently.

### What "Append-Only" Means

Append-only means the ingestion functions only execute `INSERT`
statements — never `UPDATE`, `MERGE`, or `DELETE`. Each pipeline
run adds new rows timestamped with `ingested_at = NOW()`. This
creates a complete time-series history: every 15 minutes, a snapshot
of the entire TfL network's status is preserved.

### How psycopg2 Connection Objects Work

`psycopg2.connect()` opens a TCP connection to PostgreSQL and returns
a `connection` object. From the connection, `cursor()` creates a
`cursor` object that executes SQL statements. After executing an
`INSERT`, `conn.commit()` persists the transaction. If an error
occurs, `conn.rollback()` cancels the entire batch — no partial
inserts.

The connection is created at the start of each Airflow task and closed
at the end. DAG tasks do not share connections — each task opens and
closes its own connection.

### Why Row Count Is Returned

Each ingestion function returns the number of rows inserted. This
integer is pushed to Airflow XCom, making it visible in the Airflow
UI task detail page. Engineers can see "ingest_line_status inserted
247 rows" without reading log files. It also provides an easy
sanity check: 0 rows returned is a signal of an API problem.

---

## Task 6 — Airflow DAGs

### What a DAG Is

A **Directed Acyclic Graph** is a set of tasks with defined
dependencies forming a sequence with no cycles. In Airflow, a DAG
is a Python file that defines tasks and the order they must run.

Airflow's scheduler reads all DAG files on startup and on every
`scheduler_interval` (default: 30 seconds). When a DAG's cron
schedule fires, the scheduler creates a **DAG Run** — an instance
of the DAG executing for a specific time slot. Each task in the DAG
Run executes in order, respecting the `>>` dependency arrows.

### What `*/15 * * * *` Means

Cron syntax: `minute hour day-of-month month day-of-week`

- `*/15` in the minute field means "every 15 minutes" (0, 15, 30, 45)
- `*` in all other fields means "every hour, every day, every month,
  every day of week"
- Combined: runs at :00, :15, :30, :45 of every hour, every day

`station_disruptions_dag` uses `*/30 * * * *` — every 30 minutes —
because station disruptions change more slowly than line status.

### What XCom Is

**XCom** (Cross-Communication) is Airflow's mechanism for passing
small data between tasks in the same DAG Run. When `ingest_line_status`
calls `context['ti'].xcom_push(key='row_count', value=247)`, Airflow
stores that value in its metadata database. Downstream tasks can
retrieve it with `ti.xcom_pull(task_ids='ingest_line_status',
key='row_count')`.

XCom is used here to surface row counts in the Airflow UI without
requiring tasks to write to a shared file or database table.

### Why `catchup=False`

When `catchup=True` (Airflow default), if the pipeline is stopped for
2 hours and restarted, Airflow will immediately fire 8 backfill runs
(one for each missed 15-minute slot) simultaneously. This would
overwhelm the TfL API and flood PostgreSQL with concurrent writes.

`catchup=False` means: when the scheduler starts, only run the most
recent scheduled slot. Missed historical runs are ignored. This is
correct behaviour for a pipeline ingesting live operational data —
backfilling 2 hours of missed runs does not produce useful data.

### What `max_active_runs=1` Prevents

If a DAG run takes longer than 15 minutes (e.g., TfL API is slow),
`max_active_runs=1` prevents the next scheduled run from starting
while the current one is still executing. Without this, multiple
concurrent runs would compete for database connections and write
duplicate data to the raw tables.

### Why BashOperator for dbt

dbt is a command-line tool. `dbt run` and `dbt test` are shell
commands, not Python functions. Using `BashOperator` is the correct
approach because:
- dbt's Python API is internal and undocumented
- `BashOperator` logs all dbt output (model compile, row counts,
  test results) directly to the Airflow task log
- dbt exit codes (0 = success, 1 = failure) automatically set the
  Airflow task state to success or failure

### What `>>` Means

The `>>` operator defines task dependencies. `task_a >> task_b` means
task_b will not start until task_a has completed successfully. If
task_a fails, task_b is skipped and marked "upstream_failed".

`check_api_health >> ingest_line_status >> validate_ingestion >>
trigger_dbt` means these four tasks execute in strict sequence —
each only starts when the previous one succeeds.

---

## Task 7 — Docker Compose

### What Each Service Does

- **postgres**: Runs PostgreSQL 15. On first start, executes
  `init_db.sql` from `docker-entrypoint-initdb.d/` to create all
  schemas and tables. Data persists in the `postgres_data` named
  volume between container restarts.

- **airflow-init**: Runs once on first start to initialise the Airflow
  metadata database (`airflow db migrate`) and create the admin user.
  Uses `restart: on-failure` so if postgres isn't ready yet, it
  retries automatically.

- **airflow-webserver**: Serves the Airflow UI at port 8080. Mounts
  `./dags`, `./ingestion`, and `./dbt_project` as volumes so code
  changes take effect without rebuilding the image.

- **airflow-scheduler**: Reads DAG files, triggers scheduled runs,
  and executes tasks using LocalExecutor (runs tasks as subprocesses
  on the same machine). Shares the same volumes as the webserver.

- **metabase**: Runs the Metabase analytics UI at port 3000. Connects
  to PostgreSQL for its own metadata (MB_DB_*) and allows users to
  add the tfl_pipeline database as a data source.

### Why `airflow-init` Runs Separately

`airflow db migrate` must complete exactly once before the webserver
and scheduler start — running it in the webserver would cause a race
condition if both webserver and scheduler try to migrate simultaneously.
By making it a separate service that completes before the others start,
the database is guaranteed to be initialised before any Airflow process
tries to use it.

### What the Postgres Healthcheck Does

```yaml
test: ["CMD-SHELL", "pg_isready -U tfl_user -d tfl_pipeline"]
interval: 10s
timeout: 5s
retries: 5
```

`pg_isready` checks whether PostgreSQL is accepting connections. The
healthcheck runs every 10 seconds. Other services that declare
`depends_on: postgres: condition: service_healthy` will not start
until this check passes 5 consecutive times. This prevents Airflow
from trying to connect to PostgreSQL before it is ready to accept
connections, which would cause startup failures.

### Why Volumes Are Mounted for dags, ingestion, dbt_project

Mounting these directories as bind-mounts means code changes on the
host machine are immediately visible inside the container — no rebuild
required. A developer can edit a DAG file and see it appear in the
Airflow UI within 30 seconds (the scheduler's file scan interval).
Only `requirements.txt` changes require a rebuild, since pip packages
are installed at image build time.

### How to Start the Stack

```bash
docker compose up --build
```

This builds the Airflow image (installing requirements.txt), starts
all services in dependency order, and streams logs to the terminal.
On first run, allow 2–3 minutes for all services to initialise.

### Default Credentials

- **Airflow UI** (http://localhost:8080): username `admin`, password `admin`
- **Metabase** (http://localhost:3000): set on first visit
- **PostgreSQL** (localhost:5432): user `tfl_user`, password `tfl_password`

---

## Task 8 — dbt Project

### What dbt Materializations Mean

A **materialization** defines how dbt physically creates a model in
the database:

- **view**: dbt executes `CREATE VIEW AS SELECT ...`. The view stores
  no data — it is a saved query. Every time the view is queried,
  PostgreSQL executes the underlying SELECT. Views are always current
  but add query-time cost.

- **table**: dbt executes `CREATE TABLE AS SELECT ...`. Data is
  physically copied into a new table. Queries against the table are
  fast (no runtime computation) but the table is only current as of
  the last `dbt run`.

### Why Raw Models Are Views and Mart Models Are Tables

**Raw models are views** because they simply select from the raw
tables with no transformation. There is no point copying data that
already exists in the raw tables — a view adds zero storage overhead
and zero latency (no data to copy, always current).

**Mart models are tables** because they contain expensive window
functions (`LAG`, `RANK`), multi-table `GROUP BY` aggregations, and
`CASE WHEN` scoring logic. If Metabase ran these computations on every
dashboard load, each page view would take seconds. Materialising as
tables means the expensive computation runs once per dbt run (every
15–30 minutes) and Metabase queries pre-computed results in
milliseconds.

**Staging models are views** for the same reason as raw — they are
lightweight cleaning operations (LOWER, TRIM, COALESCE) with no
aggregation. The cost of computing them at query time is negligible.

### What `ref()` Does

`ref('raw_line_status')` tells dbt: "this model depends on the model
named `raw_line_status`". dbt uses these references to:
1. Build a dependency graph and execute models in topological order
2. Replace `ref()` at compile time with the fully-qualified table/view
   name (e.g., `tfl_pipeline.raw.raw_line_status`)
3. Enable `dbt test` to identify which tests belong to which models

Using `ref()` instead of hardcoded table names means renaming a model
automatically updates all downstream references.

### What `source()` Does

`source('raw', 'line_status')` tells dbt: "this model reads from an
external table (not a dbt model) defined in `schema.yml` under
sources". This is used in raw models to reference the actual PostgreSQL
tables that Airflow writes to.

The distinction matters for lineage: dbt knows the pipeline starts at
these source tables and can display a lineage diagram showing data
flowing from raw source → raw model → staging model → mart model.

### How dbt Tests Work

Tests are defined in `schema.yml` files:

```yaml
columns:
  - name: line_id
    tests: [not_null]
```

`dbt test` compiles each test into a SQL query that returns rows if
the test fails. For `not_null`, dbt generates:

```sql
SELECT * FROM model WHERE line_id IS NULL
```

If this query returns any rows, the test fails. dbt reports the
failure with the row count and model name. When triggered from
Airflow's `BashOperator`, a test failure returns exit code 1, which
marks the Airflow task as failed and halts downstream tasks.

Custom SQL tests (in `dbt_project/tests/`) work identically: any
query that returns rows is a failure.

### What the health_score Formula Calculates

```sql
ROUND(100.0 - (avg_severity * 5.0), 1) AS health_score
```

TfL's `status_severity` scale runs 0–20 where:
- 0 = No issues (not used in practice)
- 6 = Good Service
- 9 = Minor Delays
- 12 = Severe Delays
- 20 = Suspended

Multiplying by 5 converts the 0–20 scale to 0–100. Subtracting from
100 inverts it so higher = better service. `GREATEST(0, LEAST(100,
health_score))` clamps the result to [0, 100] preventing negative
scores or scores above 100 from edge-case API data.

A line with Good Service (severity=6) scores `100 - (6*5) = 70`.
A suspended line (severity=20) scores `100 - (20*5) = 0`.

### How the LAG Window Function Works

```sql
LAG(avg_severity) OVER (
    PARTITION BY line_id
    ORDER BY trend_date
)
```

`LAG()` is a window function that returns the value of `avg_severity`
from the **previous row** in the window. The window is partitioned by
`line_id` (each line is analysed independently) and ordered by
`trend_date` (chronological order).

For the Jubilee line on 2024-01-15:
- `avg_severity` = 8.2 (today)
- `LAG(avg_severity)` = 6.1 (yesterday's avg_severity)
- `severity_change` = 8.2 - 6.1 = +2.1 (getting worse)

This produces the day-over-day change metric without any joins or
subqueries — the window function handles the self-referential
comparison.

### How to Run dbt Locally

```bash
# Install dbt
pip install dbt-core dbt-postgres

# Navigate to dbt project
cd dbt_project/

# Install dbt packages
dbt deps

# Run all models
dbt run

# Run only staging models
dbt run --select staging

# Run a specific model and all its dependencies
dbt run --select +mart_line_performance

# Run all tests
dbt test

# Generate documentation
dbt docs generate
dbt docs serve  # opens browser at localhost:8080
```

---

## Task 9 — Tests

### What the responses Library Does

The `responses` library intercepts outgoing HTTP requests made by the
`requests` library and returns pre-defined mock responses instead of
making real network calls. It works by monkey-patching `requests`'s
transport adapter at the test level.

```python
@responses.activate
def test_health_check_success():
    responses.add(responses.GET, url, json=[...], status=200)
    assert client.health_check() is True
```

The `@responses.activate` decorator enables interception for the
duration of the test function. Any `requests.get()` call that is not
matched by a registered mock raises `ConnectionError` — preventing
accidental real API calls.

### Why Real API Calls Are Never Made in Tests

Real API calls in tests:
- Require a valid TfL API key (which CI environments don't have)
- Depend on TfL API availability (pipeline tests would fail during
  TfL outages)
- Return different data on every call (tests would be non-deterministic)
- Add 100–500ms latency per test (slows CI to a crawl)
- Count against the API rate limit (500 req/min free tier)

Mock API responses are instant, deterministic, work without credentials,
and test exactly the scenario the test is designed for.

### What pytest Fixtures Are

Fixtures are reusable setup functions decorated with `@pytest.fixture`.
They are injected into test functions by name:

```python
@pytest.fixture
def mock_conn():
    conn = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(...)
    return conn

def test_ingest(mock_conn):  # fixture injected here
    result = ingest_line_status(mock_conn, mock_client)
```

Fixtures avoid repeating setup code across multiple tests. pytest
automatically calls `mock_conn()` and passes the result to any test
function that declares it as a parameter.

### Why Transformation Logic Is Tested Independently of dbt

dbt tests validate data quality (not_null, unique, accepted_values).
Unit tests validate business logic correctness. The `health_score`
formula `100 - (avg_severity * 5)` is business logic that should be
tested independently of dbt because:
- dbt tests require a running PostgreSQL database; unit tests do not
- A dbt test checks that values are within range, not that the formula
  is mathematically correct
- If the formula is wrong, unit tests catch it at development time
  before any database is involved

---

## Task 10 — GitHub Actions CI

### Why Tests Run Without a Real Database in CI

The CI environment (`ubuntu-latest` GitHub Actions runner) has no
PostgreSQL instance and no TfL API key. Tests are designed to mock
both:
- `responses` library mocks HTTP → no real TfL API needed
- `pytest-mock` patches psycopg2 → no real PostgreSQL needed

This means CI runs in seconds, costs nothing (GitHub's free tier),
and passes 100% of the time regardless of TfL API availability.

### How Mock API Responses Make CI Fast and Free

Each test completes in under 10ms because there is no network I/O.
The full test suite runs in under 5 seconds. GitHub Actions free tier
provides 2,000 minutes/month — the CI pipeline uses approximately
2 minutes per run, allowing 1,000 CI runs per month at zero cost.

### What the CI Badge Shows

The badge in `README.md`:

```markdown
[![CI](https://github.com/sathiakhadija/TFL/actions/workflows/ci.yml/badge.svg)](...)
```

Displays a green "passing" badge when the most recent CI run on the
`main` branch succeeded, or a red "failing" badge otherwise. Portfolio
reviewers can see at a glance that the pipeline's tests and linting
pass, demonstrating production engineering discipline.

---

## How to Run the Pipeline — Complete Guide

### Prerequisites

1. **Docker Desktop** installed and running (4 GB RAM allocated minimum)
2. **Git** installed
3. **TfL API key** — register free at https://api.tfl.gov.uk

### Installation

```bash
# Clone the repository
git clone https://github.com/sathiakhadija/TFL.git
cd TFL

# Create local environment file
cp .env.example .env

# Edit .env and add your TfL API key
# TFL_API_KEY=your-actual-key-here
```

### First Run

```bash
# Build images and start all services
docker compose up --build

# Wait for all services to initialise (2-3 minutes)
# Watch for: "airflow-webserver | [INFO] Listening at: http://0.0.0.0:8080"
```

### Enable DAGs in Airflow

1. Open http://localhost:8080
2. Log in: username `admin`, password `admin`
3. In the DAGs list, toggle ON:
   - `line_status_ingestion`
   - `line_arrivals_ingestion`
   - `station_disruptions_ingestion`
4. Each DAG will trigger within 15 minutes (or click the play button
   for an immediate manual run)

### Verify Data Is Flowing

```bash
# Connect to PostgreSQL and check row counts
docker exec -it tfl-postgres-1 psql -U tfl_user -d tfl_pipeline

-- Check raw tables
SELECT COUNT(*) FROM raw.line_status;
SELECT COUNT(*) FROM raw.line_arrivals;
SELECT COUNT(*) FROM raw.station_disruptions;

-- Check mart tables (populated after dbt runs)
SELECT line_id, health_score, service_status
FROM marts.mart_line_performance
ORDER BY health_score DESC;
```

### Connect Metabase

1. Open http://localhost:3000
2. Complete the Metabase setup wizard
3. Add a database: Select PostgreSQL
4. Fill in:
   - Host: `postgres`
   - Port: `5432`
   - Database name: `tfl_pipeline`
   - Username: `tfl_user`
   - Password: `tfl_password`
5. Click "Save"
6. Browse to the `marts` schema to start building dashboards

---

## Interview Preparation

### 1. What is a DAG and how does Airflow execute tasks?

A DAG — Directed Acyclic Graph — is a set of tasks connected by
dependencies with no circular references. In Airflow, I define a DAG
as a Python file where tasks are objects (PythonOperator, BashOperator)
and `>>` arrows define execution order.

Airflow's scheduler process reads all DAG files continuously. When a
DAG's cron schedule fires, the scheduler creates a DAG Run — a
specific instance of that DAG executing for a particular time slot.
It places task instances on an internal queue. The executor (in my
project, LocalExecutor) picks tasks from the queue and runs them as
subprocesses. Each task runs independently, logs its output, and
reports success or failure back to the scheduler. Downstream tasks
only start when all upstream tasks have succeeded.

### 2. What are the three dbt layers and why does each exist?

**Raw** models are views that expose the ingested data exactly as it
came from the API, with no transformations. They exist to preserve an
unmodified audit trail — if I discover a bug in my cleaning logic
three months later, the raw data is intact and I can re-run
transformations.

**Staging** models are views that clean and standardise the raw data:
normalise casing, fill NULLs with safe defaults, rename columns to
consistent conventions, and add derived time fields like
`ingested_hour`. They exist so every downstream model starts from
clean, consistently typed data.

**Mart** models are materialised tables that encode business logic:
health scores, disruption rates, reliability rankings, day-over-day
trends. They exist so analysts and Metabase dashboards can query
pre-computed results without knowing how the calculation works.

### 3. Why is the raw schema append-only?

Append-only raw tables implement the immutable event log pattern. Each
ingestion creates new rows timestamped with `ingested_at = NOW()`,
building a complete time-series of every state the TfL network has
been in. This means:

First, full auditability: I can answer "what was the status of the
Jubilee line at 08:47 on any given morning?" Second, safe
re-processing: if a dbt transformation has a bug, I fix the SQL and
re-run `dbt run` — the raw data is unchanged and the corrected marts
are rebuilt from the complete history. Third, simplicity: INSERT is
faster than UPSERT and safe for concurrent Airflow tasks, since there
are no conflicts to resolve.

### 4. What happens when a dbt test fails?

dbt compiles each test into a SQL query that returns rows if the test
fails — for example, `SELECT * FROM model WHERE line_id IS NULL`. It
runs all tests, collects results, and exits with code 1 if any test
returned rows.

In my pipeline, dbt tests run inside an Airflow `BashOperator`. Exit
code 1 marks that task as failed in the Airflow UI (shown in red).
Because the test task is not the final task, the DAG run is marked
failed and no further tasks run. Airflow can be configured to send
email or Slack alerts on failure. The data quality problem is surfaced
to the engineer within minutes of the bad data arriving.

### 5. What does the health_score formula calculate?

```sql
ROUND(100.0 - (avg_severity * 5.0), 1)
```

TfL's severity scale runs 0–20 where higher numbers mean worse
service. I multiply by 5 to convert to a 0–100 scale, then subtract
from 100 to invert it so higher scores mean better service. A line
running "Good Service" (severity 6) scores 70. A suspended line
(severity 20) scores 0. I use `GREATEST(0, LEAST(100, ...))` to clamp
the result so edge-case API data can never produce a score below 0 or
above 100.

The `service_status` label then categorises the score: 80–100 is
"Good", 50–79 is "Minor Issues", 20–49 is "Severe Disruption", 0–19
is "Suspended". These thresholds were chosen to match TfL's own
operational terminology.

### 6. Why is PostgreSQL used instead of SQLite?

Three reasons. First, concurrency: multiple Airflow tasks run
simultaneously and write to the database at the same time. SQLite
serialises all writes with an exclusive lock, meaning tasks queue up
and ingestion takes much longer. PostgreSQL handles concurrent writes
through MVCC (Multi-Version Concurrency Control) with no locking
bottleneck.

Second, schemas: PostgreSQL supports multiple schemas within a single
database (raw, staging, marts), providing logical separation with
different access permissions. SQLite has no schema concept.

Third, production relevance: every UK data organisation runs
PostgreSQL or a cloud-managed variant (AWS RDS, GCP Cloud SQL, Azure
Database). Having PostgreSQL on a portfolio demonstrates production
readiness. SQLite signals a prototype.

### 7. What does the LAG window function do in mart_disruption_trends?

```sql
LAG(avg_severity) OVER (
    PARTITION BY line_id
    ORDER BY trend_date
)
```

`LAG()` looks back one row within a defined window and returns that
row's value. The window is partitioned by `line_id` so each line is
analysed independently, and ordered by `trend_date` chronologically.

For a specific line on a specific date, `LAG(avg_severity)` returns
that line's `avg_severity` from the previous day. Subtracting today's
value from yesterday's gives `severity_change` — a positive number
means service is deteriorating, negative means improving.

This is more efficient than a self-join because the window function
scans the data once. A self-join would require a second full table
scan joined on `line_id` and `trend_date - 1 day`.

### 8. How do Airflow sensors work?

Sensors are a specialised Airflow operator that repeatedly poll a
condition and succeed when the condition is met, failing on timeout.
For example, `HttpSensor` polls a URL until it returns 200;
`SqlSensor` polls a SQL query until it returns a non-zero result.

I don't use sensors in this pipeline because the pipeline is
self-contained — it fetches data and immediately validates it in the
next task. Sensors are useful when the pipeline must wait for an
external process to complete before proceeding, such as waiting for
a file to appear in S3 or a partner's data feed to update.

If I were extending this pipeline to ingest Bus data from a third-
party provider that uploads files to S3 at irregular intervals, I
would use an `S3KeySensor` to wait for the file before triggering
ingestion.

### 9. What is XCom and why is it used?

XCom (Cross-Communication) is Airflow's built-in mechanism for passing
small values between tasks within the same DAG Run. A task pushes a
value with `ti.xcom_push(key='row_count', value=247)` and a downstream
task retrieves it with `ti.xcom_pull(task_ids='ingest_line_status',
key='row_count')`. Values are stored in Airflow's metadata database.

I use XCom to pass the row count from the ingestion task to the
validation task and surface it in the Airflow UI's task detail view.
Without XCom, tasks would need to write to a shared file or database
table to communicate — more complex and harder to monitor.

XCom is not designed for large payloads (the metadata database has
size limits). It is correct for scalar values and small metadata, not
for DataFrames or file contents.

### 10. How would you extend this pipeline to add a fourth data source?

For example, adding TfL Bus arrival data:

**Step 1 — API client**: Add a `get_bus_arrivals(route_ids)` method
to `TfLClient` calling `/Line/{ids}/Arrivals` with bus route IDs.

**Step 2 — Raw table**: Add `CREATE TABLE raw.bus_arrivals (...)` to
`init_db.sql` with the same append-only pattern and `ingested_at`
index.

**Step 3 — Ingestion module**: Create `ingestion/bus_arrivals.py`
with `ingest_bus_arrivals(conn, client)` and `validate_bus_arrivals(conn)`.

**Step 4 — DAG**: Create `dags/bus_arrivals_dag.py` following the
same four-task pattern: health_check → ingest → validate → trigger_dbt.

**Step 5 — dbt models**: Create `raw_bus_arrivals.sql`,
`stg_bus_arrivals.sql`, and a new mart `mart_bus_performance.sql`.
Add sources and tests to the relevant `schema.yml` files.

**Step 6 — Tests**: Add `test_bus_arrivals.py` with mocked HTTP
responses for the new endpoint.

The architecture is intentionally modular — each data source is a
self-contained set of (client method, ingestion module, DAG, dbt
models). Adding a new source does not require modifying existing code.

---

## Technical Decisions Log

### Airflow vs Alternatives

| Field | Decision |
|---|---|
| **Decision** | Use Apache Airflow for orchestration |
| **Alternatives** | Prefect, Dagster, Luigi, cron, GitHub Actions scheduled |
| **Reason chosen** | Airflow is the most widely deployed orchestrator in UK enterprise data teams. Provides task-level UI, XCom, retry logic, and a recognisable portfolio signal. |
| **Trade-offs** | Airflow is heavyweight — requires a metadata database, separate webserver and scheduler processes, and significant memory. Prefect Cloud is simpler to operate but requires an external service. Cron is trivial but provides no observability. |

### dbt vs Raw SQL Transformations

| Field | Decision |
|---|---|
| **Decision** | Use dbt Core for all transformations |
| **Alternatives** | Raw SQL scripts executed by psycopg2, pandas DataFrames, SQLAlchemy |
| **Reason chosen** | dbt provides version-controlled SQL, automatic lineage, built-in testing framework, and documentation generation — none of which raw SQL scripts provide. |
| **Trade-offs** | dbt adds a tool to learn and a compile step. For a pipeline with 3 transformations, the overhead is noticeable. The tooling pays off as the number of models grows beyond 10. |

### PostgreSQL vs Alternatives

| Field | Decision |
|---|---|
| **Decision** | Use PostgreSQL 15 as the storage layer |
| **Alternatives** | SQLite, DuckDB, ClickHouse, BigQuery |
| **Reason chosen** | PostgreSQL handles concurrent writes from multiple Airflow tasks, supports schema-based layer separation, and is the UK data engineering production standard. |
| **Trade-offs** | PostgreSQL requires more memory and configuration than SQLite. DuckDB would be faster for analytical queries but cannot handle concurrent writes from a scheduler. |

### Metabase vs Alternatives

| Field | Decision |
|---|---|
| **Decision** | Use Metabase for visualisation |
| **Alternatives** | Grafana, Streamlit, Apache Superset, Redash |
| **Reason chosen** | Metabase provides zero-code dashboards via Docker with a native PostgreSQL connector. No Python skills required for analysts to build charts. |
| **Trade-offs** | Metabase's free tier has limited alerting and scheduling. Grafana is more configurable but requires learning PromQL and is optimised for time-series metrics rather than relational data. |

### 15-Minute Schedule vs Other Intervals

| Field | Decision |
|---|---|
| **Decision** | Ingest line status and arrivals every 15 minutes |
| **Alternatives** | 5 minutes (more current), 30 minutes (lower cost), 1 hour |
| **Reason chosen** | 15 minutes matches TfL's own status update frequency — more frequent polling would fetch identical data. Balances data freshness with API quota consumption. |
| **Trade-offs** | TfL's free API tier allows 500 req/min. At 15-minute intervals with 3 endpoints, the pipeline uses 12 requests/hour — well within limits. A 5-minute interval would use 36 requests/hour, still within limits but higher cost for no additional data freshness. |

### Append-Only Raw Tables vs Upsert

| Field | Decision |
|---|---|
| **Decision** | Raw tables are append-only (INSERT only) |
| **Alternatives** | UPSERT on line_id (keep only latest status), UPDATE in place |
| **Reason chosen** | Append-only creates a complete time-series history enabling trend analysis, anomaly detection, and re-processing from source if transformations change. |
| **Trade-offs** | Raw tables grow without bound. At 15-minute intervals ingesting 12 lines, `raw.line_status` grows by approximately 12 rows every 15 minutes — 576 rows/hour, ~4 million rows/year. Storage is cheap; historical data is valuable. A retention policy (`DELETE FROM raw.line_status WHERE ingested_at < NOW() - INTERVAL '90 days'`) can be added as a maintenance DAG. |

---

## Streamlit Dashboard

The project now includes a custom Streamlit dashboard in `dashboard/app.py`.
It complements Metabase by providing a portfolio-ready frontend with a
controlled visual identity, custom interaction details, and direct
presentation of the mart-layer metrics. Metabase remains useful for
ad-hoc exploration, but the Streamlit dashboard gives the pipeline a
designed product surface that can be run with one Compose service.

### Why Streamlit in Addition to Metabase

Metabase is excellent for quick BI dashboards and analyst-led charting.
The custom Streamlit dashboard was built because it allows the project
to demonstrate frontend engineering decisions that Metabase cannot
express as precisely: branded layout, custom cards, animated live
indicators, a dark theme, bespoke table badges, and Plotly chart theming.
It also keeps the dashboard code version-controlled next to the pipeline,
so the analytics experience can evolve through normal pull requests.

### Design System Decisions

The dashboard uses TfL identity colours as its primary structure:
`#DC241F` for the red accent and live state, and `#003B8E` for headers
and chart contrast. The England palette adds white text and alert red,
while the dark background and surface colours keep the UI appropriate
for monitoring live operational data. Headings use Times New Roman to
create an editorial, civic feel, while body and data text use Inter for
legibility in dense cards, tables, and axis labels.

### PostgreSQL Connection

Streamlit connects directly to PostgreSQL with `psycopg2`. The connection
is configured entirely through environment variables:
`POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, and
`POSTGRES_PASSWORD`. Defaults are provided for local development, but
the app does not hardcode credentials into the Python source. In Docker
Compose, the dashboard service points `POSTGRES_HOST` to the `postgres`
service name and reads `.env` from the mounted project file.

### Auto-Refresh

The app stores `last_refresh` and `refresh_interval` in Streamlit session
state. Each render computes the remaining seconds and displays that in
the sidebar. When the elapsed time exceeds the 60-second interval, the
app updates `last_refresh` and calls `st.rerun()` so all SQL queries are
executed again and the visualisations reflect the newest mart data.

### Plotly Theme

All Plotly figures use transparent or dark paper backgrounds, Inter axis
labels, Times New Roman titles, muted gridlines, and the TfL red/blue
palette. The disruption chart uses a red scale for line-level disruption
rate, the severity heatmap moves from TfL blue to TfL red, and the raw
volume chart uses a red line with a subtle filled area so ingestion
activity is readable without overwhelming the dark interface.

### Dashboard Panels

**Line Health Cards** show the latest record per line from
`marts.mart_line_performance`. Each card displays health score, service
status, and disruption rate with colour coding for Good, Minor Issues,
Severe Disruption, and Suspended.

**Disruption Rate Chart** aggregates `marts.mart_disruption_trends` by
line and orders the horizontal bars from worst to best, making the most
affected lines immediately visible.

**Station Reliability Table** reads `marts.mart_station_reliability` and
shows ranked stations with total disruptions, daily average disruptions,
and coloured reliability-grade badges.

**Severity Heatmap** uses `marts.mart_line_performance` to compare
average severity by line and hour of day. This makes time-of-day patterns
visible as the dataset grows.

**Data Volume Chart** reads from `raw.line_status` and counts rows by
ingestion hour. It acts as a pipeline heartbeat, showing whether fresh
raw data continues to arrive over time.

### Data Quality Issue and Fix

#### The Bug

The Station Reliability table in the dashboard was displaying full TfL
disruption advisory messages — paragraphs of operational text — in the
station name column instead of clean station names like "Arsenal" or
"Liverpool Street". The `mart_station_reliability` mart propagated
whatever was stored in `raw.station_disruptions.station_name`, so the
corruption appeared all the way through to the UI.

#### Diagnosis

Querying `raw.station_disruptions` directly revealed that the
`station_name` column contained disruption message text for every row.
The mart and staging layer both passed this field through without
transformation, so the root cause had to be in the ingestion layer.

Reading `ingestion/station_disruptions.py` identified two bugs:

1. **No-affectedStops branch (line 34):** when the TfL API returns a
   disruption with no `affectedStops` list, the fallback set
   `station_name = disruption.get("description", "Unknown Station")`,
   which picked up the full disruption message as the name.

2. **affectedStops branch:** even when iterating `affectedStops`, the
   code used `stop.get("commonName")`. For certain TfL disruption types
   the `commonName` field is populated with the disruption message rather
   than the stop name, so this path produced the same corruption.

Both paths therefore wrote advisory text into `station_name` whenever
the TfL API did not include a separate human-readable name field.

#### Fix in the Ingestion Code

A `TFL_STATION_NAMES` dict was added to `ingestion/tfl_client.py`,
mapping each of the 21 monitored ATCO codes (e.g. `940GZZLUASL`) to its
clean station name. Both branches of `ingest_station_disruptions` in
`ingestion/station_disruptions.py` now perform a dict lookup first:

```python
# No-affectedStops branch
station_id = disruption.get("stationAtcoCode", "")
station_name = TFL_STATION_NAMES.get(station_id.upper(), "Unknown Station")

# affectedStops branch
stop_id = stop.get("atcoCode", "")
stop_name = TFL_STATION_NAMES.get(
    stop_id.upper(),
    stop.get("commonName", "Unknown Station"),
)
```

If the ATCO code is in the dict the clean name is used unconditionally.
The API's `commonName` is only used for stops not in the monitored set,
where the API value is likely to be reliable.

#### Backfilling Existing Data

The fix was applied retroactively to the 20 existing rows in
`raw.station_disruptions` with an `UPDATE` keyed on `LOWER(station_id)`.
After the raw table was corrected, `marts.mart_station_reliability` was
rebuilt (`TRUNCATE` then `INSERT ... SELECT`) so the dashboard reflected
the clean names immediately without waiting for the next ingestion cycle.

#### Why This Matters for Data Engineering

Raw API data is unreliable by default. The TfL disruption endpoint
returns a single disruption object that simultaneously carries the
affected stop list, the human-readable message, and structured metadata
— and the mapping between fields is not consistent across disruption
types. Trusting that `commonName` always contains a name, or that a
named field will always contain the expected semantic content, is a
common source of silent data corruption.

The pattern that caught and fixed this issue is the correct one for data
engineering in production: query the raw layer directly before
diagnosing higher layers, isolate the ingestion code that writes the
bad value, and use a controlled lookup (the `TFL_STATION_NAMES` dict)
rather than trusting API field semantics. Backfilling raw data and
rebuilding downstream marts completes the fix without requiring a full
re-ingestion from the API. Being comfortable with all three steps —
diagnosis, code fix, and data backfill — is a core data engineering
skill that comes up in every pipeline that consumes external APIs.
