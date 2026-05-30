SELECT *
FROM {{ ref('stg_line_status') }}
WHERE status_severity < 0
   OR status_severity > 20
