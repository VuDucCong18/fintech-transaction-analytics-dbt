{{ config(materialized='table') }}

with accounts as (
    select
        account_id,
        customer_id,
        account_type,
        account_currency,
        available_balance,
        credit_limit,
        account_status,
        account_is_active,
        opened_date,
        closed_date,
        is_joint_account,
        dbt_loaded_at

    from {{ ref('stg_accounts') }}
)

select * from accounts
