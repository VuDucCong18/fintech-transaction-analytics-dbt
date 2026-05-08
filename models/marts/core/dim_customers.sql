{{ config(materialized='table') }}

with customers as (
    select
        customer_id,
        first_name,
        last_name,
        full_name,
        email,
        phone_number,
        date_of_birth,
        gender,
        nationality,
        country_of_residence,
        city,
        signup_date,
        signup_month,
        customer_age,
        kyc_status,
        risk_rating,
        customer_segment,
        is_active,
        dbt_loaded_at

    from {{ ref('stg_customers') }}
)

select * from customers
