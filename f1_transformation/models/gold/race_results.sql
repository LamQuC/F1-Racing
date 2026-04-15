{{ config(
    materialized='incremental',
    unique_key=['year', 'event_name', 'driver']
) }}

WITH base_stats AS (
    SELECT 
        year,
        event_name,
        driver,
        AVG(speed) as avg_speed,
        MAX(speed) as max_speed
    FROM {{ ref('stg_f1_telemetry') }}
    GROUP BY 1, 2, 3
)
SELECT 
    *,
    RANK() OVER (PARTITION BY year, event_name ORDER BY avg_speed DESC) as rank
FROM base_stats