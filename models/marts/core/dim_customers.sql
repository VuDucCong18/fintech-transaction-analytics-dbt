{{ config(materialized='table') }}

/*
    dim_customers
    Grain: one row per customer_id (SCD Type 1 — latest state only).
    Enriched with derived analytical attributes for BI consumption.
    Source: stg_customers (cast, renamed, cleaned from RAW_CUSTOMERS).
*/

with customers as (

    select
        customer_id,
        customer_name,
        email,
        gender,
        date_of_birth,
        country,
        city,
        signup_date,
        signup_month,
        customer_age,
        kyc_status,
        kyc_is_verified,
        customer_segment,
        created_at,
        dbt_loaded_at

    from {{ ref('stg_customers') }}

),

enriched as (

    select
        *,

        -- Age banding for cohort analysis and demographic segmentation
        case
            when customer_age < 26  then 'Gen Z (18-25)'
            when customer_age < 36  then 'Millennial (26-35)'
            when customer_age < 51  then 'Gen X (36-50)'
            else                         'Boomer+ (51+)'
        end                                                     as age_band,

        -- How long they have been a customer, in days
        datediff('day', signup_date, current_date())            as account_tenure_days,

        -- Flag customers who signed up within the last 12 months
        case
            when datediff('day', signup_date, current_date()) <= 365
            then true else false
        end                                                     as is_recent_signup,

        -- Simplified KYC tier for reporting
        case
            when kyc_is_verified and kyc_status = 'VERIFIED' then 'Fully Verified'
            when kyc_status = 'PENDING'                       then 'Pending Review'
            else                                                   'Unverified'
        end                                                     as kyc_tier

    from customers

)

select * from enriched
