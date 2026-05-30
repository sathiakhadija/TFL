{{ config(materialized='table', schema='marts') }}
WITH disruption_counts AS (
    SELECT
        station_id,
        station_name,
        disruption_date,
        COUNT(*)                       AS daily_disruptions,
        COUNT(DISTINCT disruption_type) AS disruption_types,
        COUNT(DISTINCT category)       AS categories
    FROM {{ ref('stg_station_disruptions') }}
    GROUP BY station_id, station_name, disruption_date
),
station_totals AS (
    SELECT
        station_id,
        station_name,
        COUNT(DISTINCT disruption_date) AS days_with_disruptions,
        SUM(daily_disruptions)         AS total_disruptions,
        AVG(daily_disruptions)         AS avg_daily_disruptions,
        MAX(daily_disruptions)         AS max_daily_disruptions
    FROM disruption_counts
    GROUP BY station_id, station_name
)
SELECT
    station_id,
    station_name,
    days_with_disruptions,
    total_disruptions,
    ROUND(avg_daily_disruptions, 2)    AS avg_daily_disruptions,
    max_daily_disruptions,
    RANK() OVER (
        ORDER BY total_disruptions DESC
    )                                  AS disruption_rank,
    CASE
        WHEN total_disruptions = 0     THEN 'Excellent'
        WHEN total_disruptions <= 5    THEN 'Good'
        WHEN total_disruptions <= 15   THEN 'Fair'
        ELSE 'Poor'
    END                                AS reliability_grade
FROM station_totals
ORDER BY total_disruptions DESC
