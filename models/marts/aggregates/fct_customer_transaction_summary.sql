{{ config(materialized='table') }}

with customer_summary as (
    select
        customer_id,
        count(*) as total_transactions,
        count(case when is_successful then 1 end) as successful_transactions,
        count(case when is_failed then 1 end) as failed_transactions,
        count(case when is_pending then 1 end) as pending_transactions,
        sum(transaction_amount_sgd) as total_spend_sgd,
        sum(case when is_successful then fee_amount_sgd else 0 end) as total_fee_generated_sgd,
        min(transaction_date) as first_transaction_date,
        max(transaction_date) as last_transaction_date,
        count(distinct transaction_date) as active_transaction_days,
        count(case when is_cross_border then 1 end) as cross_border_transactions,
        -- Most used channel
        mode() within group (order by channel) as preferred_channel,
        -- Most used transaction type
        mode() within group (order by transaction_type) as most_used_transaction_type,
        current_timestamp() as dbt_loaded_at

    from {{ ref('fact_transactions') }}
    group by 1
)

select * from customer_summary
