{{ config(materialized='view') }}

with source_data as (
    select
        transaction_id,
        customer_id,
        account_id,
        card_id,
        merchant_id,
        transaction_timestamp,
        -- Derived fields from timestamp
        cast(transaction_timestamp as date) as transaction_date,
        date_trunc('month', transaction_timestamp) as transaction_month,
        upper(trim(transaction_type)) as transaction_type,
        cast(transaction_amount as numeric(18, 2)) as transaction_amount,
        upper(trim(transaction_currency)) as transaction_currency,
        cast(fee_amount as numeric(18, 2)) as fee_amount,
        upper(trim(transaction_status)) as transaction_status,
        upper(trim(channel)) as channel,
        is_cross_border,
        lower(trim(failure_reason)) as failure_reason,
        created_at,
        current_timestamp() as dbt_loaded_at

    from {{ source('fintech_raw', 'RAW_TRANSACTIONS') }}
)

select * from source_data
