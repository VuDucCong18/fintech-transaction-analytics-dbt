{{ config(materialized='view') }}

with source_data as (
    select
        merchant_id,
        trim(merchant_name) as merchant_name,
        upper(trim(merchant_category)) as merchant_category,
        upper(trim(merchant_country)) as merchant_country,
        upper(trim(merchant_city)) as merchant_city,
        onboarding_date,
        upper(trim(merchant_status)) as merchant_status,
        -- Derived field: Flag for active merchants
        case 
            when upper(trim(merchant_status)) = 'ACTIVE' then true
            else false
        end as merchant_is_active,
        created_at,
        current_timestamp() as dbt_loaded_at

    from {{ source('fintech_raw', 'raw_merchants') }}
)

select * from source_data
