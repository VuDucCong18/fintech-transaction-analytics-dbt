{{ config(materialized='view') }}

with source_data as (
    select
        customer_id,
        trim(first_name) as first_name,
        trim(last_name) as last_name,
        concat(trim(first_name), ' ', trim(last_name)) as full_name,
        lower(trim(email)) as email,
        phone_number,
        date_of_birth,
        gender,
        nationality,
        country_of_residence,
        city,
        signup_date,
        upper(trim(customer_segment)) as customer_segment,
        upper(trim(kyc_status)) as kyc_status,
        upper(trim(risk_rating)) as risk_rating,
        is_active,
        -- Derived field: Calculate customer age in years from date of birth
        case 
            when date_of_birth is not null 
            then year(current_date()) - year(date_of_birth)
            else null
        end as customer_age,
        -- Extract signup month for cohort analysis
        date_trunc('month', signup_date) as signup_month,
        created_at,
        current_timestamp() as dbt_loaded_at

    from {{ source('fintech_raw', 'RAW_CUSTOMERS') }}
)

select * from source_data
