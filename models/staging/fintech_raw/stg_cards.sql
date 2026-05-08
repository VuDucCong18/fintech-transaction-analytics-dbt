{{ config(materialized='view') }}

with source_data as (
    select
        card_id,
        account_id,
        upper(trim(card_type)) as card_type,
        upper(trim(card_network)) as card_network,
        daily_limit,
        upper(trim(card_status)) as card_status,
        issued_date,
        expiry_date,
        is_virtual,
        -- Derived field: Flag for active cards (not expired and not blocked/cancelled)
        case 
            when upper(trim(card_status)) = 'ACTIVE' 
                 and expiry_date >= current_date() 
            then true
            else false
        end as card_is_active,
        created_at,
        current_timestamp() as dbt_loaded_at

    from {{ source('fintech_raw', 'raw_cards') }}
)

select * from source_data
