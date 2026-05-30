import logging
from datetime import datetime, timezone

from ingestion.tfl_client import TfLClient

logger = logging.getLogger(__name__)


def ingest_line_status(conn, client: TfLClient) -> int:
    """
    Fetch line status from TfL API and insert into raw.line_status.
    conn: psycopg2 connection object
    Returns number of rows inserted.
    Handles the nested lineStatuses list in TfL response.
    One row per line status entry (a line can have multiple statuses).
    Logs each line processed.
    """
    line_statuses = client.get_line_status()
    ingested_at = datetime.now(timezone.utc)
    rows_inserted = 0

    with conn.cursor() as cur:
        for line in line_statuses:
            line_id = line.get("id", "")
            line_name = line.get("name", "")
            status_entries = line.get("lineStatuses", [])

            logger.info(
                "Processing line %s (%s): %d status entries",
                line_id, line_name, len(status_entries)
            )

            for status in status_entries:
                disruption = status.get("disruption") or {}
                cur.execute(
                    """
                    INSERT INTO raw.line_status (
                        line_id, line_name, status_severity,
                        status_severity_description, reason,
                        disruption_category, disruption_description,
                        ingested_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        line_id,
                        line_name,
                        status.get("statusSeverity", 0),
                        status.get("statusSeverityDescription"),
                        status.get("reason"),
                        disruption.get("category"),
                        disruption.get("description"),
                        ingested_at,
                    )
                )
                rows_inserted += 1

    conn.commit()
    logger.info("Inserted %d rows into raw.line_status", rows_inserted)
    return rows_inserted


def validate_line_status(conn) -> dict:
    """
    Validate the most recent ingestion batch.
    Checks:
      - Row count > 0 in last 5 minutes
      - No null line_ids in last batch
      - Status severity values are between 0 and 20
    Returns dict with keys: valid (bool), checks (dict), row_count (int).
    """
    checks = {}

    with conn.cursor() as cur:
        # Check 1: row count in last 5 minutes
        cur.execute(
            """
            SELECT COUNT(*)
            FROM raw.line_status
            WHERE ingested_at >= NOW() - INTERVAL '5 minutes'
            """
        )
        row_count = cur.fetchone()[0]
        checks["recent_rows_exist"] = row_count > 0

        # Check 2: no null line_ids in last batch
        cur.execute(
            """
            SELECT COUNT(*)
            FROM raw.line_status
            WHERE ingested_at >= NOW() - INTERVAL '5 minutes'
              AND line_id IS NULL
            """
        )
        null_line_ids = cur.fetchone()[0]
        checks["no_null_line_ids"] = null_line_ids == 0

        # Check 3: severity values in valid range 0-20
        cur.execute(
            """
            SELECT COUNT(*)
            FROM raw.line_status
            WHERE ingested_at >= NOW() - INTERVAL '5 minutes'
              AND (status_severity < 0 OR status_severity > 20)
            """
        )
        out_of_range = cur.fetchone()[0]
        checks["severity_in_range"] = out_of_range == 0

    valid = all(checks.values())
    logger.info("line_status validation: valid=%s checks=%s row_count=%d", valid, checks, row_count)

    return {
        "valid": valid,
        "checks": checks,
        "row_count": row_count,
    }
