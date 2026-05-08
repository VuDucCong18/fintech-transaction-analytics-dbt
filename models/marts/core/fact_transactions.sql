{{ config(materialized='table') }}

with transactions as (
    select
        t.transaction_id,
        t.customer_id,
        t.account_id,
        t.card_id,
        t.merchant_id,
        t.transaction_date,
        t.transaction_month,
        t.transaction_type,
        t.transaction_status,
        t.channel,
        t.failure_reason,
        t.transaction_amount,
        t.transaction_currency,
        t.fee_amount,
        a.account_currency,
        -- Signed transaction amount logic for cashflow
        -- Outflows: Purchase, Withdrawal, Transfer = negative
        -- Inflows: Deposit, Refund = positive
        case 
            when t.transaction_type in ('Purchase', 'Withdrawal', 'Transfer') 
            then -1 * t.transaction_amount
            when t.transaction_type in ('Deposit', 'Refund') 
            then t.transaction_amount
            else 0  -- fallback for unknown types
        end as signed_transaction_amount,
        -- FX conversion to SGD for transaction amount
        case
            when t.transaction_currency = 'SGD' 
            then t.transaction_amount
            else t.transaction_amount * coalesce(fx_latest.exchange_rate, fx_default.exchange_rate, 1.0)
        end as transaction_amount_sgd,
        -- FX conversion to SGD for fee amount
        case
            when t.transaction_currency = 'SGD' 
            then t.fee_amount
            else t.fee_amount * coalesce(fx_latest.exchange_rate, fx_default.exchange_rate, 1.0)
        end as fee_amount_sgd,
        -- Status flags for easy filtering
        case when t.transaction_status = 'Success' then true else false end as is_successful,
        case when t.transaction_status = 'Failed' then true else false end as is_failed,
        case when t.transaction_status = 'Pending' then true else false end as is_pending,
        -- Cross-border flag: Already in source data
        t.is_cross_border,
        t.dbt_loaded_at

    from {{ ref('stg_transactions') }} t
    left join {{ ref('stg_accounts') }} a 
        on t.account_id = a.account_id
    -- Join for FX rate on exact transaction date
    left join {{ ref('stg_fx_rates') }} fx_latest
        on t.transaction_currency = fx_latest.from_currency
        and fx_latest.to_currency = 'SGD'
        and t.transaction_date = fx_latest.rate_date
    -- Join for fallback FX rate (latest rate before transaction date)
    left join {{ ref('stg_fx_rates') }} fx_default
        on t.transaction_currency = fx_default.from_currency
        and fx_default.to_currency = 'SGD'
        and fx_latest.rate_id is null  -- only if exact date not found
        and fx_default.rate_date = (
            select max(rate_date)
            from {{ ref('stg_fx_rates') }}
            where from_currency = t.transaction_currency
            and to_currency = 'SGD'
            and rate_date <= t.transaction_date
        )
)

select * from transactions
