{{ config(materialized='view', schema='raw') }}
SELECT
    id,
    station_id,
    station_name,
    disruption_type,
    category,
    description,
    additional_info,
    ingested_at
FROM {{ source('raw', 'station_disruptions') }}
