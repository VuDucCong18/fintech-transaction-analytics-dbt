{{ config(materialized='view') }}

with source_data as (

    select
        customer_id,
        trim(customer_name) as customer_name,
        lower(trim(email)) as email,
        upper(trim(gender)) as gender,
        date_of_birth,
        upper(trim(country)) as country,
        trim(city) as city,
        signup_date,
        upper(trim(customer_segment)) as customer_segment,
        upper(trim(kyc_status)) as kyc_status,

        case 
            when upper(trim(kyc_status)) = 'VERIFIED' then true
            else false
        end as kyc_is_verified,

        case 
            when date_of_birth is not null 
            then datediff('year', date_of_birth, current_date())
            else null
        end as customer_age,

        date_trunc('month', signup_date) as signup_month,

        created_at,
        current_timestamp() as dbt_loaded_at

    from {{ source('fintech_raw', 'RAW_CUSTOMERS') }}

)

select *
from source_data
