# Fintech Transaction Analytics - dbt Project

A production-grade **Analytics Engineering** project demonstrating a complete end-to-end fintech customer transaction analytics pipeline. Built with **Snowflake** and **dbt** following modern data engineering best practices.

## 📊 Project Overview

This project builds a scalable, well-tested data transformation layer that takes raw fintech transaction data and transforms it into analytics-ready tables for BI dashboards, reporting, and data science applications.

### Key Characteristics
- **Layered Architecture**: RAW → STAGING → MARTS for clear separation of concerns
- **Production Ready**: Comprehensive tests, documentation, and data quality checks
- **BI Optimized**: Fact and dimension tables designed for dashboard performance
- **Modular Design**: Reusable components with clear dependencies via dbt refs
- **Well Documented**: Extensive YAML documentation useful for analytics and business users

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│   Snowflake FINTECH_ANALYTICS Database  │
├─────────────────────────────────────────┤
│                                         │
│  RAW Schema (Loaded externally)         │
│  ├── RAW_CUSTOMERS                      │
│  ├── RAW_ACCOUNTS                       │
│  ├── RAW_CARDS                          │
│  ├── RAW_MERCHANTS                      │
│  ├── RAW_FX_RATES                       │
│  └── RAW_TRANSACTIONS                   │
│                                         │
│  STAGING Schema (dbt Views)             │
│  ├── STG_CUSTOMERS                      │
│  ├── STG_ACCOUNTS                       │
│  ├── STG_CARDS                          │
│  ├── STG_MERCHANTS                      │
│  ├── STG_FX_RATES                       │
│  └── STG_TRANSACTIONS                   │
│                                         │
│  MARTS Schema (dbt Tables)              │
│  ├── CORE                               │
│  │   ├── DIM_CUSTOMERS (Dimension)      │
│  │   ├── DIM_ACCOUNTS (Dimension)       │
│  │   ├── DIM_CARDS (Dimension)          │
│  │   ├── DIM_MERCHANTS (Dimension)      │
│  │   └── FACT_TRANSACTIONS (Fact)       │
│  │                                      │
│  └── AGGREGATES                         │
│      ├── FCT_DAILY_TRANSACTION_SUMMARY  │
│      └── FCT_CUSTOMER_TRANSACTION_SUMMARY
│                                         │
└─────────────────────────────────────────┘
```

---

## 📚 Data Model

### Staging Layer (STAGING Schema)

The staging layer cleans and prepares raw data with minimal business logic:

- **stg_customers**: Clean customer profile data with calculated age and signup cohorts
- **stg_accounts**: Clean account details with active account flags
- **stg_cards**: Clean card information with validity flags
- **stg_merchants**: Clean merchant data with active status
- **stg_fx_rates**: Exchange rates for multi-currency conversion to SGD
- **stg_transactions**: Clean transaction data with derived date fields

**Key Transformations**:
- Column name standardization (snake_case, lowercase)
- Data type casting
- String standardization (UPPER, lower, TRIM)
- Simple derived fields (is_active flags, dates from timestamps)
- NULL handling

### Mart Layer (MARTS Schema)

#### Core Dimensions (Star Schema)

**dim_customers**
- One row per customer
- Profile: name, email, country, city, phone
- Business: segment, KYC status, signup date
- Metrics: age-in-years

**dim_accounts**
- One row per account
- Type, currency, balance, status
- Timeline: opened_date, closed_date
- Flag: account_is_active

**dim_cards**
- One row per card
- Type, network, credit_limit
- Validity: issued_date, expiry_date
- Flag: card_is_active (not expired, active status)

**dim_merchants**
- One row per merchant
- Business: name, category, country, city
- Status: merchant_is_active, onboarding_date

**fact_transactions** (Central Fact Table)
- One row per transaction
- Foreign keys: customer_id, account_id, card_id, merchant_id
- Transaction details: type, status, channel, failure_reason
- Amounts: transaction_amount (original currency), fee_amount
- **FX Converted**: transaction_amount_sgd, fee_amount_sgd
  - Joins dynamically to stg_fx_rates on transaction_date
  - Falls back to latest available rate if exact date unavailable
- **Signed Amounts**: signed_transaction_amount
  - Outflows (PURCHASE, WITHDRAWAL, TRANSFER) = negative
  - Inflows (DEPOSIT, REFUND) = positive
- **Status Flags**: is_successful, is_failed, is_pending
- **Cross-Border Flag**: is_cross_border (transaction_currency != account_currency)

#### Aggregate Tables

**fct_daily_transaction_summary**
- Grain: transaction_date, transaction_currency, channel, transaction_status
- Metrics:
  - transaction_count, successful_transaction_count, failed_transaction_count
  - total_transaction_amount, total_transaction_amount_sgd
  - total_fee_amount, total_fee_amount_sgd
  - success_rate, failed_rate
  - cross_border_transaction_count

**fct_customer_transaction_summary**
- Grain: customer_id
- Metrics:
  - total_transactions, successful/failed/pending breakdown
  - total_spend_sgd, total_fee_generated_sgd
  - first/last transaction dates, active_transaction_days
  - cross_border_transactions
  - preferred_channel, most_used_transaction_type

---

## 🎯 Business Questions Supported

This data model enables analytics for:

### Customer Analytics
- Customer lifecycle: signup date, first transaction, active days
- Customer segmentation: segment, KYC status, spending patterns
- Customer value: lifetime spend, transaction frequency

### Transaction Analytics
- Daily volume & value by currency, channel, and status
- Success vs failure rates by channel
- Cross-border transaction monitoring
- Fee revenue metrics

### Merchant Analytics
- Top merchants and categories
- Merchant performance
- Merchant onboarding & status tracking

### Fintech Operations
- Payment channel effectiveness
- Transaction status trends
- currency exposure and conversion
- Fraud pattern detection (via failure reasons)

---

## 📂 Project Structure

```
fintech-transaction-analytics-dbt/
├── dbt_project.yml                 # dbt project configuration
├── README.md                       # This file
│
├── models/
│   ├── staging/
│   │   └── fintech_raw/
│   │       ├── _sources.yml        # Source table definitions
│   │       ├── schema.yml          # Staging model documentation
│   │       ├── stg_customers.sql
│   │       ├── stg_accounts.sql
│   │       ├── stg_cards.sql
│   │       ├── stg_merchants.sql
│   │       ├── stg_fx_rates.sql
│   │       └── stg_transactions.sql
│   │
│   └── marts/
│       ├── core/
│       │   ├── dim_customers.sql
│       │   ├── dim_accounts.sql
│       │   ├── dim_cards.sql
│       │   ├── dim_merchants.sql
│       │   └── fact_transactions.sql
│       │
│       ├── aggregates/
│       │   ├── fct_daily_transaction_summary.sql
│       │   └── fct_customer_transaction_summary.sql
│       │
│       └── schema.yml              # Mart documentation & tests
│
├── tests/                          # (Optional custom tests)
├── macros/                         # (Optional dbt macros)
└── seeds/                          # (Optional seed data)
```

---

## 🔧 Setup & Installation

### Prerequisites
- Snowflake account with database `FINTECH_ANALYTICS`
- Snowflake warehouse `FINTECH_WH`
- Raw tables pre-populated in `FINTECH_ANALYTICS.RAW`
- dbt CLI installed (`pip install dbt-snowflake`)

### Installation

1. **Clone repository**
   ```bash
   git clone https://github.com/yourusername/fintech-transaction-analytics-dbt.git
   cd fintech-transaction-analytics-dbt
   ```

2. **Create dbt profile** (usually in `~/.dbt/profiles.yml`)
   ```yaml
   fintech_transaction_analytics:
     target: dev
     outputs:
       dev:
         type: snowflake
         account: [your-account-id]
         user: [your-username]
         password: [your-password]
         role: ANALYST_ROLE
         database: FINTECH_ANALYTICS
         warehouse: FINTECH_WH
         schema: analytics_dev
         threads: 4
   ```

3. **Install dbt packages** (if using dbt-expectations)
   ```bash
   dbt deps
   ```

---

## 🚀 Running dbt

### Basic Commands

**Parse project & test connection**
```bash
dbt debug
```

**Run all models**
```bash
dbt run
```

**Run with tests**
```bash
dbt build
```

**Run specific model**
```bash
dbt run --select stg_customers
```

**Run staging models only**
```bash
dbt run --select path:models/staging
```

**Run marts after staging**
```bash
dbt run --select path:models/marts
```

**Build documentation**
```bash
dbt docs generate
```

**Serve documentation locally**
```bash
dbt docs serve
```

### Full Test & Build Pipeline

```bash
# Recommended workflow
dbt parse                          # Parse project
dbt test --select source          # Test sources
dbt run --select path:models/staging    # Build staging
dbt run --select path:models/marts      # Build marts
dbt test                           # Run all tests
dbt docs generate                  # Generate docs
```

---

## ✅ Testing & Data Quality

The project includes comprehensive test coverage:

### Test Types

**Uniqueness & Nullability** (Primary Keys)
- All primary keys tested for uniqueness and NOT NULL
- Foreign keys tested for NOT NULL

**Referential Integrity** (Relationships)
- fact_transactions.customer_id → dim_customers.customer_id
- fact_transactions.account_id → dim_accounts.account_id
- fact_transactions.card_id → dim_cards.card_id
- fact_transactions.merchant_id → dim_merchants.merchant_id

**Accepted Values** (Enums)
- transaction_status: SUCCESS, FAILED, PENDING
- transaction_type: PURCHASE, REFUND, DEPOSIT, WITHDRAWAL, TRANSFER
- channel: MOBILE, WEB, ATM, BRANCH, API
- kyc_status: VERIFIED, PENDING, REJECTED

**Numeric Constraints**
- transaction_amount >= 0
- fee_amount >= 0
- exchange_rate is numeric

**View test coverage**
```bash
dbt test
dbt test --select stg_transactions  # Test specific model
dbt test --select tag:critical      # Test by tag (optional)
```

---

## 📖 Documentation

This project includes extensive documentation:

### YAML Documentation
- **_sources.yml**: All raw table definitions with column descriptions
- **schema.yml** (staging): Staging model specs and tests
- **schema.yml** (marts): Dimension & fact table specs, relationships, tests

### Building & Viewing Docs

```bash
# Generate documentation
dbt docs generate

# Serve docs locally
dbt docs serve
# Open http://localhost:8000 in browser
```

The documentation includes:
- Model descriptions and purposes
- Column definitions and business logic
- Source table lineage
- Test configurations
- Lineage graphs

---

## 🔑 Key Features

### 1. **Dimensional Modeling**
- Star schema with conformed dimensions
- Single fact table for transactions
- Aggregate tables for performance

### 2. **Multi-Currency Support**
- All transactions converted to SGD using FX rates
- Handles missing FX rates by falling back to latest available rate
- Supports future expansion to other base currencies

### 3. **Transaction Signing Logic**
- Intelligent signed amounts for cash flow analysis
- Purchase/Withdrawal/Transfer = negative/outflow
- Deposit/Refund = positive/inflow
- Maintains raw amounts for reconciliation

### 4. **Data Quality**
- 40+ automated tests
- Relationship integrity checks
- NULL/uniqueness constraints

### 5. **Performance Optimized**
- Staging views for minimal storage
- Aggregates for common queries
- Indexing-friendly grain

### 6. **BI Friendly**
- Clear naming conventions
- Boolean flags for easy filtering
- Pre-computed aggregates

---

## 🎓 Learning Resources

### dbt Concepts Used
- **Source** macro: `{{ source('fintech_raw', 'raw_customers') }}`
- **Ref** macro: `{{ ref('stg_customers') }}`
- **CTE-based SQL**: Common Table Expressions for readability
- **Config blocks**: Materialization, schema overrides
- **Testing**: Data tests via YAML configuration
- **Macros**: (Optional) Custom macro examples

### SQL Patterns
- LEFT JOINs for dimensional conformity
- Window functions (RANK, ROW_NUMBER)
- Aggregate functions (SUM, COUNT, MAX, MIN)
- CASE statements for business logic
- Date/timestamp functions

---

## 🚧 Future Improvements

### Near-term (Phase 2)
- Add snapshot tables for SCD Type 2 (customer/merchant changes)
- Create incremental models for large fact tables
- Add dbt macros for common transformations
- Implement custom dbt tests for business logic

### Medium-term (Phase 3)
- Add data lineage and impact analysis
- Implement CI/CD pipeline (GitHub Actions)
- Add performance monitoring and run time tracking
- Create sentinel tables for monitoring data freshness

### Long-term (Phase 4)
- Add predictive models (customer churn, fraud detection)
- Implement reverse ETL for operational data
- Add real-time streaming capabilities
- Create data governance and cataloging layer

---

## 👤 Author

Built as a portfolio project to demonstrate Analytics Engineering best practices with:
- dbt (data build tool)
- Snowflake (cloud data warehouse)
- SQL (transformation logic)
- YAML (documentation & configuration)

---

## 📄 License

This project is open source and available under the MIT License.

---

## 📞 Support & Contact

For questions, improvements, or contributions:
- Review the `dbt docs` for detailed column definitions
- Check `models/marts/schema.yml` for all test specifications
- Examine model SQL files for transformation logic

---

## 🔑 Key Metrics & KPIs Enabled

This data model directly supports:

| Metric | Query | Mart Used |
|--------|-------|-----------|
| Daily Transaction Volume | COUNT(*) GROUP BY transaction_date | fct_daily_transaction_summary |
| Daily Revenue | SUM(transaction_amount_sgd), SUM(fee_amount_sgd) | fct_daily_transaction_summary |
| Success Rate | successful_transaction_count / transaction_count | fct_daily_transaction_summary |
| Top Merchants | JOIN fact_transactions + dim_merchants | dim_merchants + fact_transactions |
| Customer LTV | SUM(total_spend_sgd) GROUP BY customer_id | fct_customer_transaction_summary |
| Active Customers | COUNT(DISTINCT customer_id) WHERE last_transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) | fct_customer_transaction_summary |
| Cross-Border Volume | COUNT(*) WHERE is_cross_border = TRUE | fact_transactions |
| Fee Revenue | SUM(fee_amount_sgd) | fct_daily_transaction_summary |

---

**Happy analyzing! 📊**
