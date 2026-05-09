{{ config(materialized='table') }}

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

)

select *
from customers
