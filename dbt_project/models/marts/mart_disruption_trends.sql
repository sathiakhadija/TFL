{{ config(materialized='table', schema='marts') }}
WITH daily_line_disruptions AS (
    SELECT
        ingested_date                  AS trend_date,
        line_id,
        line_name,
        COUNT(*)                       AS total_readings,
        AVG(status_severity)           AS avg_severity,
        MAX(status_severity)           AS peak_severity,
        SUM(
            CASE WHEN status_severity > 6
            THEN 1 ELSE 0 END
        )                              AS disrupted_readings,
        COUNT(DISTINCT disruption_category) AS unique_categories
    FROM {{ ref('stg_line_status') }}
    GROUP BY ingested_date, line_id, line_name
)
SELECT
    trend_date,
    line_id,
    line_name,
    total_readings,
    ROUND(avg_severity, 2)             AS avg_severity,
    peak_severity,
    disrupted_readings,
    unique_categories,
    ROUND(
        100.0 * disrupted_readings
        / NULLIF(total_readings, 0), 1
    )                                  AS disruption_rate_pct,
    LAG(avg_severity) OVER (
        PARTITION BY line_id
        ORDER BY trend_date
    )                                  AS prev_day_severity,
    ROUND(
        avg_severity - LAG(avg_severity) OVER (
            PARTITION BY line_id
            ORDER BY trend_date
        ), 2
    )                                  AS severity_change
FROM daily_line_disruptions
ORDER BY trend_date DESC, line_id
