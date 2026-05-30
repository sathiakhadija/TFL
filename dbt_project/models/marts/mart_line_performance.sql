{{ config(materialized='table', schema='marts') }}
WITH hourly_status AS (
    SELECT
        line_id,
        line_name,
        ingested_hour,
        ingested_date,
        AVG(status_severity)           AS avg_severity,
        MAX(status_severity)           AS max_severity,
        MIN(status_severity)           AS min_severity,
        COUNT(*)                       AS status_readings,
        SUM(
            CASE WHEN status_severity > 6
            THEN 1 ELSE 0 END
        )                              AS disrupted_readings,
        COUNT(DISTINCT disruption_category) AS disruption_types
    FROM {{ ref('stg_line_status') }}
    GROUP BY line_id, line_name, ingested_hour, ingested_date
),
with_health_score AS (
    SELECT
        *,
        ROUND(
            100.0 - (avg_severity * 5.0), 1
        )                              AS health_score,
        ROUND(
            100.0 * disrupted_readings
            / NULLIF(status_readings, 0), 1
        )                              AS disruption_rate_pct
    FROM hourly_status
)
SELECT
    line_id,
    line_name,
    ingested_hour,
    ingested_date,
    avg_severity,
    max_severity,
    min_severity,
    status_readings,
    disrupted_readings,
    disruption_types,
    GREATEST(0, LEAST(100, health_score)) AS health_score,
    disruption_rate_pct,
    CASE
        WHEN health_score >= 80 THEN 'Good'
        WHEN health_score >= 50 THEN 'Minor Issues'
        WHEN health_score >= 20 THEN 'Severe Disruption'
        ELSE 'Suspended'
    END                                AS service_status
FROM with_health_score
