{{ config(materialized='view') }}

with source_data as (

    select
        account_id,
        customer_id,
        upper(trim(account_type)) as account_type,
        upper(trim(account_status)) as account_status,
        opened_date,
        closed_date,
        upper(trim(account_currency)) as account_currency,
        current_balance,

        case 
            when upper(trim(account_status)) = 'ACTIVE' then true
            else false
        end as account_is_active,

        created_at,
        current_timestamp() as dbt_loaded_at

    from {{ source('fintech_raw', 'RAW_ACCOUNTS') }}

)

select *
from source_data
