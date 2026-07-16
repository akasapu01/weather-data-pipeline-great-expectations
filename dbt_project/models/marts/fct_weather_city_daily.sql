-- Daily weather summary per city: the analytics-ready fact table.

with hourly as (

    select * from {{ ref('stg_hourly_observations') }}

)

select
    city,
    country,
    observed_date,
    count(*)                       as hours_observed,
    round(avg(temperature_c), 2)   as avg_temperature_c,
    round(min(temperature_c), 2)   as min_temperature_c,
    round(max(temperature_c), 2)   as max_temperature_c,
    round(avg(humidity_pct), 2)    as avg_humidity_pct,
    round(avg(wind_speed_kmh), 2)  as avg_wind_speed_kmh,
    round(sum(precipitation_mm), 2) as total_precipitation_mm,
    max(extracted_at)              as last_extracted_at
from hourly
group by 1, 2, 3
