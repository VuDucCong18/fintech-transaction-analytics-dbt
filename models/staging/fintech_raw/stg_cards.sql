{{ config(materialized='view') }}

with source_data as (

    select
        card_id,
        customer_id,
        account_id,
        upper(trim(card_type)) as card_type,
        upper(trim(card_network)) as card_network,
        upper(trim(card_status)) as card_status,
        issued_date,
        expiry_date,
        credit_limit,

        case 
            when upper(trim(card_status)) = 'ACTIVE'
                 and expiry_date >= current_date()
            then true
            else false
        end as card_is_active,

        created_at,
        current_timestamp() as dbt_loaded_at

    from {{ source('fintech_raw', 'RAW_CARDS') }}

)

select *
from source_data
