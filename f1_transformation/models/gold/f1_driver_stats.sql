{{ config(materialized='view') }}

SELECT 
    year,
    event_name,
    driver,
    gear,
    ROUND(AVG(speed), 2) as avg_speed,
    MAX(speed) as max_speed,
    COUNT(*) as total_records
FROM {{ ref('stg_f1_telemetry') }}
GROUP BY 1, 2, 3, 4
ORDER BY year, event_name, gear