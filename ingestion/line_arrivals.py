import logging
from datetime import datetime, timezone

from ingestion.tfl_client import TfLClient

logger = logging.getLogger(__name__)


def ingest_line_arrivals(conn, client: TfLClient) -> int:
    """
    Fetch arrival predictions and insert into raw.line_arrivals.
    Returns number of rows inserted.
    Filters out arrivals where time_to_station < 0.
    Parses expectedArrival ISO8601 string to datetime.
    Logs total arrivals fetched per line.
    """
    arrivals = client.get_line_arrivals()
    ingested_at = datetime.now(timezone.utc)
    rows_inserted = 0

    by_line: dict[str, int] = {}
    filtered = 0

    with conn.cursor() as cur:
        for arrival in arrivals:
            time_to_station = arrival.get("timeToStation", -1)

            if time_to_station < 0:
                filtered += 1
                continue

            line_id = arrival.get("lineId", "")
            by_line[line_id] = by_line.get(line_id, 0) + 1

            expected_arrival_raw = arrival.get("expectedArrival")
            expected_arrival = None
            if expected_arrival_raw:
                try:
                    expected_arrival = datetime.fromisoformat(
                        expected_arrival_raw.replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    logger.warning("Could not parse expectedArrival: %s", expected_arrival_raw)

            cur.execute(
                """
                INSERT INTO raw.line_arrivals (
                    vehicle_id, line_id, line_name,
                    station_id, station_name, platform_name,
                    destination_id, destination_name,
                    time_to_station, expected_arrival, ingested_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    arrival.get("vehicleId"),
                    line_id,
                    arrival.get("lineName"),
                    arrival.get("naptanId", ""),
                    arrival.get("stationName", ""),
                    arrival.get("platformName"),
                    arrival.get("destinationNaptanId"),
                    arrival.get("destinationName"),
                    time_to_station,
                    expected_arrival,
                    ingested_at,
                )
            )
            rows_inserted += 1

    conn.commit()

    for line_id, count in by_line.items():
        logger.info("Line %s: %d arrivals ingested", line_id, count)

    logger.info(
        "Inserted %d rows into raw.line_arrivals (%d filtered as departed)",
        rows_inserted, filtered
    )
    return rows_inserted


def validate_line_arrivals(conn) -> dict:
    """
    Validate most recent arrivals batch.
    Checks:
      - Row count > 0 in last 5 minutes
      - No negative time_to_station values
      - At least 8 distinct lines represented
    Returns validation result dict.
    """
    checks = {}

    with conn.cursor() as cur:
        # Check 1: row count in last 5 minutes
        cur.execute(
            """
            SELECT COUNT(*)
            FROM raw.line_arrivals
            WHERE ingested_at >= NOW() - INTERVAL '5 minutes'
            """
        )
        row_count = cur.fetchone()[0]
        checks["recent_rows_exist"] = row_count > 0

        # Check 2: no negative time_to_station
        cur.execute(
            """
            SELECT COUNT(*)
            FROM raw.line_arrivals
            WHERE ingested_at >= NOW() - INTERVAL '5 minutes'
              AND time_to_station < 0
            """
        )
        negative_times = cur.fetchone()[0]
        checks["no_negative_wait_times"] = negative_times == 0

        # Check 3: at least 8 distinct lines
        cur.execute(
            """
            SELECT COUNT(DISTINCT line_id)
            FROM raw.line_arrivals
            WHERE ingested_at >= NOW() - INTERVAL '5 minutes'
            """
        )
        distinct_lines = cur.fetchone()[0]
        checks["sufficient_line_coverage"] = distinct_lines >= 8

    valid = all(checks.values())
    logger.info("line_arrivals validation: valid=%s checks=%s row_count=%d", valid, checks, row_count)

    return {
        "valid": valid,
        "checks": checks,
        "row_count": row_count,
    }
