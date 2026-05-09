{{ config(materialized='table') }}

with merchants as (
    select
        merchant_id,
        merchant_name,
        merchant_category,
        merchant_country,
        merchant_city,
        onboarding_date,
        merchant_status,
        merchant_is_active,
        dbt_loaded_at

    from {{ ref('stg_merchants') }}
)

select * from merchants
