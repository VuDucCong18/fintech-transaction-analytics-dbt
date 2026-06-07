{{ config(materialized='table') }}

/*
    dim_merchants
    Grain: one row per merchant_id (SCD Type 1 — latest state only).
    Enriched with derived operational attributes for BI consumption.
    Source: stg_merchants (cast, renamed, cleaned from RAW_MERCHANTS).
*/

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

),

enriched as (

    select
        *,

        -- Days since the merchant was onboarded
        datediff('day', onboarding_date, current_date())        as merchant_tenure_days,

        -- Merchants onboarded more than 365 days ago are considered established
        case
            when datediff('day', onboarding_date, current_date()) > 365
            then true else false
        end                                                     as is_established_merchant,

        -- Tenure band for segmentation and cohort analysis
        case
            when datediff('day', onboarding_date, current_date()) <= 90
                then 'New (0-90 days)'
            when datediff('day', onboarding_date, current_date()) <= 365
                then 'Growing (91-365 days)'
            when datediff('day', onboarding_date, current_date()) <= 730
                then 'Established (1-2 years)'
            else    'Mature (2+ years)'
        end                                                     as merchant_tenure_band

    from merchants

)

select * from enriched
