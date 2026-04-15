{{ config(
    materialized='incremental',
    unique_key=['driver', 'year', 'event_name', 'session_time']
) }}

SELECT
    driver,
    year,
    event_name,
    CAST(session_time AS INTERVAL) as session_time,
    speed,
    rpm,
    gear,
    throttle,
    brake,
    location_x,
    location_y
FROM {{ source('raw_data', 'f1_raw_telemetry') }}