{{ config(materialized='table') }}

with cards as (

    select
        card_id,
        customer_id,
        account_id,
        card_type,
        card_network,
        card_status,
        issued_date,
        expiry_date,
        credit_limit,
        card_is_active,
        created_at,
        dbt_loaded_at

    from {{ ref('stg_cards') }}

)

select *
from cards
