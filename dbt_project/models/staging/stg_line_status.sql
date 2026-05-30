{{ config(materialized='view', schema='staging') }}
SELECT
    id,
    LOWER(TRIM(line_id))           AS line_id,
    INITCAP(line_name)             AS line_name,
    status_severity::INTEGER       AS status_severity,
    COALESCE(
        status_severity_description,
        'Unknown'
    )                              AS status_description,
    COALESCE(reason, '')           AS disruption_reason,
    COALESCE(
        disruption_category,
        'None'
    )                              AS disruption_category,
    ingested_at                    AS _loaded_at,
    DATE_TRUNC('hour', ingested_at) AS ingested_hour,
    DATE(ingested_at)              AS ingested_date
FROM {{ ref('raw_line_status') }}
WHERE line_id IS NOT NULL
  AND status_severity IS NOT NULL
