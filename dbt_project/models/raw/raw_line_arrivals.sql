{{ config(materialized='view', schema='raw') }}
SELECT
    id,
    vehicle_id,
    line_id,
    line_name,
    station_id,
    station_name,
    platform_name,
    destination_id,
    destination_name,
    time_to_station,
    expected_arrival,
    ingested_at
FROM {{ source('raw', 'line_arrivals') }}
