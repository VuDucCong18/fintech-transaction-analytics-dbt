{{ config(materialized='table') }}

with cards as (
    select
        card_id,
        account_id,
        card_type,
        card_network,
        daily_limit,
        issued_date,
        expiry_date,
        card_status,
        is_virtual,
        card_is_active,
        dbt_loaded_at

    from {{ ref('stg_cards') }}
)

select * from cards
