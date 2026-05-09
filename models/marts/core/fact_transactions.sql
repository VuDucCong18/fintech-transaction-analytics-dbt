{{ config(materialized='table') }}

with transactions as (

    select
        t.transaction_id,
        t.customer_id,
        t.account_id,
        t.card_id,
        t.merchant_id,

        t.transaction_timestamp,
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

        case
            when t.transaction_type in ('PURCHASE', 'WITHDRAWAL', 'TRANSFER')
                then -1 * t.transaction_amount
            when t.transaction_type in ('DEPOSIT', 'REFUND')
                then t.transaction_amount
            else 0
        end as signed_transaction_amount,

        case
            when t.transaction_currency = 'SGD'
                then t.transaction_amount
            else t.transaction_amount * coalesce(fx_exact.exchange_rate, fx_fallback.exchange_rate, 1)
        end as transaction_amount_sgd,

        case
            when t.transaction_currency = 'SGD'
                then t.fee_amount
            else t.fee_amount * coalesce(fx_exact.exchange_rate, fx_fallback.exchange_rate, 1)
        end as fee_amount_sgd,

        case when t.transaction_status = 'SUCCESS' then true else false end as is_successful,
        case when t.transaction_status = 'FAILED' then true else false end as is_failed,
        case when t.transaction_status = 'PENDING' then true else false end as is_pending,

        t.is_cross_border,

        t.created_at,
        t.dbt_loaded_at

    from {{ ref('stg_transactions') }} t

    left join {{ ref('stg_accounts') }} a
        on t.account_id = a.account_id

    left join {{ ref('stg_fx_rates') }} fx_exact
        on t.transaction_currency = fx_exact.from_currency
        and fx_exact.to_currency = 'SGD'
        and t.transaction_date = fx_exact.rate_date

    left join {{ ref('stg_fx_rates') }} fx_fallback
        on t.transaction_currency = fx_fallback.from_currency
        and fx_fallback.to_currency = 'SGD'
        and fx_exact.fx_rate_id is null
        and fx_fallback.rate_date = (
            select max(sub_fx.rate_date)
            from {{ ref('stg_fx_rates') }} sub_fx
            where sub_fx.from_currency = t.transaction_currency
              and sub_fx.to_currency = 'SGD'
              and sub_fx.rate_date <= t.transaction_date
        )

)

select *
from transactions