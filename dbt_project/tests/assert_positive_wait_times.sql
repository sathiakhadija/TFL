SELECT *
FROM {{ ref('stg_line_arrivals') }}
WHERE time_to_station_seconds <= 0
