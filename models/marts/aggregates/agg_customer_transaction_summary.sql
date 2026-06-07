{{ config(materialized='table') }}

/*
    agg_customer_transaction_summary
    Grain: one row per customer_id.
    Powers the Customer Intelligence dashboard.
    Renamed from fct_customer_transaction_summary — this is an aggregate table,
    not a fact table in the Kimball sense. The fct_ prefix is reserved for
    FACT_TRANSACTIONS, which holds one row per transaction event.
*/

with customer_summary as (

    select
        customer_id,

        count(*)                                        as total_transactions,
        count_if(is_successful)                         as successful_transactions,
        count_if(is_failed)                             as failed_transactions,
        count_if(is_pending)                            as pending_transactions,

        sum(transaction_amount_sgd)                     as total_spend_sgd,
        sum(case when is_successful
                 then fee_amount_sgd else 0 end)        as total_fee_generated_sgd,

        min(transaction_date)                           as first_transaction_date,
        max(transaction_date)                           as last_transaction_date,
        count(distinct transaction_date)                as active_transaction_days,

        count_if(is_cross_border)                       as cross_border_transactions,

        round(
            {{ safe_divide(
                'count_if(is_successful) * 100.0',
                'count(*)'
            ) }},
            2
        )                                               as customer_success_rate,

        mode(channel)                                   as preferred_channel,
        mode(transaction_type)                          as most_used_transaction_type,

        current_timestamp()                             as dbt_loaded_at

    from {{ ref('fact_transactions') }}
    group by customer_id

)

select * from customer_summary
