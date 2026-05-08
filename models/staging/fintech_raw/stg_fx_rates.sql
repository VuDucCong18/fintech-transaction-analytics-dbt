{{ config(materialized='view') }}

with source_data as (
    select
        fx_rate_id,
        rate_date,
        upper(trim(from_currency)) as from_currency,
        upper(trim(to_currency)) as to_currency,
        cast(exchange_rate as numeric(18, 6)) as exchange_rate,
        created_at,
        current_timestamp() as dbt_loaded_at

    from {{ source('fintech_raw', 'raw_fx_rates') }}
)

select * from source_data
