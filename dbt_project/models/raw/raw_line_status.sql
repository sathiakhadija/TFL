{{ config(materialized='view', schema='raw') }}
SELECT
    id,
    line_id,
    line_name,
    status_severity,
    status_severity_description,
    reason,
    disruption_category,
    disruption_description,
    ingested_at
FROM {{ source('raw', 'line_status') }}
