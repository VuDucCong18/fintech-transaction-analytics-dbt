# Fintech Transaction Analytics | dbt + Snowflake Analytics Engineering Project

## Author

I am **Vu Duc Cong**

Fresh graduate from Singapore Management University (SMU)
Bachelor of Science in Information Systems, with a second major in Data Science & Analytics

I am a passionate data professional with strong interest in analytics engineering, business intelligence, and scalable data systems. This project was independently designed and built to demonstrate practical competence in:

* Git & GitHub version control workflow (branching, pull requests, production governance)
* dbt (data build tool)
* Snowflake cloud data warehousing
* SQL data transformation
* YAML documentation & testing
* End-to-end analytics engineering architecture

This repository is both a technical project and a professional portfolio touchpoint for recruiters, hiring managers, and employers to understand how I approach real-world data problems through structured engineering, testing, and business-oriented design.

---

## Project Purpose

This project showcases how raw fintech operational data can be transformed into production-grade, analytics-ready datasets using modern ELT practices.

The objective was to simulate how enterprise data teams design scalable transformation pipelines that support:

* BI dashboards
* Product analytics
* Customer behavior analysis
* Operational monitoring
* Financial reporting

---

## Technical Stack

### Core Technologies

* **dbt Core (v1.11+)** — transformation, testing, documentation
* **Snowflake** — cloud data warehouse
* **SQL** — transformation logic
* **YAML** — schema documentation & data tests
* **Git/GitHub** — version control, branching, PR governance

### Development Environment

* VS Code
* dbt Studio
* PowerShell
* Snowflake Worksheets

### Data Modeling Framework

* Dimensional Modeling (Star Schema)
* RAW → STAGING → MARTS architecture
* Fact & Dimension design
* Aggregate summary tables

---

## Project Overview

This is a production-style Analytics Engineering project that transforms raw fintech customer transaction data into BI-ready marts.

### Final Pipeline:

```text
RAW → STAGING → MARTS
```

### Raw Source Tables:

* RAW_CUSTOMERS
* RAW_ACCOUNTS
* RAW_CARDS
* RAW_MERCHANTS
* RAW_FX_RATES
* RAW_TRANSACTIONS

### Final Output:

#### Core Dimensions

* DIM_CUSTOMERS
* DIM_ACCOUNTS
* DIM_CARDS
* DIM_MERCHANTS

#### Fact Table

* FACT_TRANSACTIONS

#### Aggregate Tables

* FCT_DAILY_TRANSACTION_SUMMARY
* FCT_CUSTOMER_TRANSACTION_SUMMARY

---

## Original Architecture Diagram

```text
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

## Key Business Logic Implemented

### 1. Multi-Currency FX Conversion

All transactions are dynamically normalized into SGD using FX tables, with fallback logic when exact daily rates are unavailable.

### 2. Signed Cashflow Logic

* PURCHASE / WITHDRAWAL / TRANSFER → Negative
* DEPOSIT / REFUND → Positive

### 3. Customer Behavioral Analytics

* Total spend
* Transaction frequency
* Preferred channel
* Most used transaction type
* Cross-border usage

### 4. Data Quality Governance

* 88 dbt tests passed
* Primary key uniqueness
* Null checks
* Accepted values
* Relationship integrity

---

## Key Achievements

* Built 13 dbt models end-to-end
* Passed 88/88 data quality tests
* Implemented full Git feature branch → PR → main workflow
* Designed BI-ready dimensional model
* Built production-style schema documentation
* Applied modular, scalable SQL architecture

---

## Example Business Questions Supported

### Customer Analytics

* Who are the highest-value customers?
* What is customer lifetime spend?
* Which channels do customers prefer?

### Transaction Monitoring

* Daily transaction volume
* Failure rates by channel
* Cross-border trends
* FX-normalized revenue

### Merchant Insights

* Merchant activity
* Category trends
* Revenue contribution

---

## Repository Structure

```text
fintech-transaction-analytics-dbt/
│
├── models/
│   ├── staging/
│   └── marts/
│
├── dbt_project.yml
├── profiles.yml
└── README.md
```

---

## Running the Project

```bash
dbt debug
dbt build
dbt docs generate
dbt docs serve
```

---

## Professional Intent

As a fresh graduate entering the data industry, I built this project not simply to practice tools, but to demonstrate readiness for modern data roles through:

* Technical execution
* Business logic translation
* Documentation clarity
* Production workflow discipline

I believe strong data work is not only about writing SQL, but about designing systems that are scalable, testable, and useful for business decision-making.

---

## About Me

I am actively pursuing opportunities across:

* Data Analytics
* Analytics Engineering
* Business Intelligence
* Data Strategy

With internship experience across startup, hypergrowth, and enterprise environments, this project represents my effort to further strengthen warehouse architecture and transformation engineering capability.

---

## Contact

**Vu Duc Cong**
Singapore Management University
Bachelor of Science (Information Systems + Data Science & Analytics)

GitHub profile and project repository serve as demonstrations of my technical and analytical capability.

---

## Final Note

This project was built to reflect not just technical competency, but professional intent: the ability to design trustworthy data systems that transform raw information into strategic business value.

