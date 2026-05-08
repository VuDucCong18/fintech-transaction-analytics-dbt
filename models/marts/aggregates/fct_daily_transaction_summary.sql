{{ config(materialized='table') }}

with daily_summary as (
    select
        transaction_date,
        transaction_currency,
        channel,
        transaction_status,
        count(*) as transaction_count,
        count(case when is_successful then 1 end) as successful_transaction_count,
        count(case when is_failed then 1 end) as failed_transaction_count,
        count(case when is_pending then 1 end) as pending_transaction_count,
        sum(transaction_amount) as total_transaction_amount,
        sum(transaction_amount_sgd) as total_transaction_amount_sgd,
        sum(fee_amount) as total_fee_amount,
        sum(fee_amount_sgd) as total_fee_amount_sgd,
        count(case when is_cross_border then 1 end) as cross_border_transaction_count,
        -- Calculate success and failure rates
        round(
            100.0 * count(case when is_successful then 1 end) / nullif(count(*), 0),
            2
        ) as success_rate,
        round(
            100.0 * count(case when is_failed then 1 end) / nullif(count(*), 0),
            2
        ) as failed_rate,
        current_timestamp() as dbt_loaded_at

    from {{ ref('fact_transactions') }}
    group by 1, 2, 3, 4
)

select * from daily_summary
