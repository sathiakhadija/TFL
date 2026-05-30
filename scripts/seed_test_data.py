"""
Seed test data into the raw schema for local development and testing.
Run after init_db.sql has been applied.
Usage: python scripts/seed_test_data.py
"""
import os
from datetime import datetime, timezone, timedelta

import psycopg2

POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.environ.get("POSTGRES_DB", "tfl_pipeline")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "tfl_user")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "tfl_password")

LINES = [
    ("bakerloo", "Bakerloo"),
    ("central", "Central"),
    ("circle", "Circle"),
    ("district", "District"),
    ("jubilee", "Jubilee"),
    ("metropolitan", "Metropolitan"),
    ("northern", "Northern"),
    ("piccadilly", "Piccadilly"),
    ("victoria", "Victoria"),
    ("elizabeth", "Elizabeth"),
]

STATIONS = [
    ("940GZZLUKSX", "King's Cross St. Pancras"),
    ("940GZZLULVT", "Liverpool Street"),
    ("940GZZLUVIC", "Victoria"),
    ("940GZZLUWTA", "Waterloo"),
    ("940GZZLUOXC", "Oxford Circus"),
]


def seed(conn):
    now = datetime.now(timezone.utc)
    with conn.cursor() as cur:
        # Seed raw.line_status — 3 ingestion batches, 15 min apart
        for batch in range(3):
            ingested_at = now - timedelta(minutes=batch * 15)
            for line_id, line_name in LINES:
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
                        line_id, line_name, 10,
                        "Good Service", None, None, None,
                        ingested_at,
                    )
                )

        # Seed raw.line_arrivals
        for line_id, line_name in LINES:
            for i in range(5):
                cur.execute(
                    """
                    INSERT INTO raw.line_arrivals (
                        vehicle_id, line_id, line_name,
                        station_id, station_name,
                        time_to_station, expected_arrival, ingested_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        f"vehicle_{line_id}_{i}",
                        line_id, line_name,
                        "940GZZLUKSX", "King's Cross St. Pancras",
                        (i + 1) * 120,
                        now + timedelta(seconds=(i + 1) * 120),
                        now,
                    )
                )

    conn.commit()
    print("Seed data inserted successfully.")


if __name__ == "__main__":
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )
    try:
        seed(conn)
    finally:
        conn.close()
