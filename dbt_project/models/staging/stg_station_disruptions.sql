{{ config(materialized='view', schema='staging') }}
SELECT
    id,
    LOWER(TRIM(station_id))        AS station_id,
    COALESCE(station_name,
             'Unknown Station')    AS station_name,
    COALESCE(disruption_type,
             'Unknown')            AS disruption_type,
    COALESCE(category, 'General')  AS category,
    COALESCE(description, '')      AS description,
    ingested_at                    AS _loaded_at,
    DATE(ingested_at)              AS disruption_date,
    DATE_TRUNC('hour', ingested_at) AS disruption_hour
FROM {{ ref('raw_station_disruptions') }}
WHERE station_id IS NOT NULL
