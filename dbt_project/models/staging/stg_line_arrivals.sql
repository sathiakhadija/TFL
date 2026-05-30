{{ config(materialized='view', schema='staging') }}
SELECT
    id,
    LOWER(TRIM(line_id))           AS line_id,
    LOWER(TRIM(station_id))        AS station_id,
    COALESCE(station_name,
             'Unknown Station')    AS station_name,
    COALESCE(destination_name,
             'Unknown')            AS destination_name,
    time_to_station::INTEGER       AS time_to_station_seconds,
    ROUND(
        time_to_station / 60.0, 1
    )                              AS time_to_station_minutes,
    expected_arrival,
    ingested_at                    AS _loaded_at,
    DATE_TRUNC('hour', ingested_at) AS ingested_hour
FROM {{ ref('raw_line_arrivals') }}
WHERE time_to_station > 0
  AND line_id IS NOT NULL
  AND station_id IS NOT NULL
