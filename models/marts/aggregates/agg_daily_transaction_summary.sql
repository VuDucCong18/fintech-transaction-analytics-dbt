{{ config(materialized='table') }}

/*
    agg_daily_transaction_summary
    Grain: one row per (transaction_date, transaction_currency, channel, transaction_status).
    Powers the Executive Overview and Transaction Operations dashboards.
    Renamed from fct_daily_transaction_summary — this is an aggregate table,
    not a fact table in the Kimball sense. The fct_ prefix is reserved for
    FACT_TRANSACTIONS, which holds one row per transaction event.
*/

with daily_summary as (

    select
        transaction_date,
        transaction_currency,
        channel,
        transaction_status,

        count(*)                                              as transaction_count,
        count(case when is_successful then 1 end)            as successful_transaction_count,
        count(case when is_failed     then 1 end)            as failed_transaction_count,
        count(case when is_pending    then 1 end)            as pending_transaction_count,

        sum(transaction_amount)                              as total_transaction_amount,
        sum(transaction_amount_sgd)                          as total_transaction_amount_sgd,
        sum(fee_amount)                                      as total_fee_amount,
        sum(fee_amount_sgd)                                  as total_fee_amount_sgd,

        count(case when is_cross_border then 1 end)          as cross_border_transaction_count,

        round(
            {{ safe_divide(
                'count(case when is_successful then 1 end) * 100.0',
                'count(*)'
            ) }},
            2
        )                                                    as success_rate,

        round(
            {{ safe_divide(
                'count(case when is_failed then 1 end) * 100.0',
                'count(*)'
            ) }},
            2
        )                                                    as failed_rate,

        current_timestamp()                                  as dbt_loaded_at

    from {{ ref('fact_transactions') }}
    group by 1, 2, 3, 4

)

select * from daily_summary
