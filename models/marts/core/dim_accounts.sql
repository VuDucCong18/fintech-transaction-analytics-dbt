{{ config(materialized='table') }}

with accounts as (

    select
        account_id,
        customer_id,
        account_type,
        account_status,
        opened_date,
        closed_date,
        account_currency,
        current_balance,
        account_is_active,
        created_at,
        dbt_loaded_at

    from {{ ref('stg_accounts') }}

)

select *
from accounts
