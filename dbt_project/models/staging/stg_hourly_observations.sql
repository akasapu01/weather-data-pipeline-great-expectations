-- Cleaned, typed, de-duplicated hourly observations from the raw landing table.

with source as (

    select * from {{ source('raw_weather', 'hourly_observations') }}

),

deduped as (

    select
        city,
        country,
        cast(latitude as float64)         as latitude,
        cast(longitude as float64)        as longitude,
        timestamp(observed_at)            as observed_at,
        timestamp(extracted_at)           as extracted_at,
        cast(temperature_c as float64)    as temperature_c,
        cast(humidity_pct as float64)     as humidity_pct,
        cast(wind_speed_kmh as float64)   as wind_speed_kmh,
        cast(precipitation_mm as float64) as precipitation_mm,
        row_number() over (
            partition by city, observed_at
            order by extracted_at desc
        ) as rn
    from source

)

select
    city,
    country,
    latitude,
    longitude,
    observed_at,
    date(observed_at)  as observed_date,
    temperature_c,
    humidity_pct,
    wind_speed_kmh,
    precipitation_mm,
    extracted_at
from deduped
where rn = 1
