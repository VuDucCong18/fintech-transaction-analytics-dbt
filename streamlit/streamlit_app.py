from snowflake.snowpark import Session

@st.cache_resource
def get_session():
    return Session.builder.configs({
        "account": st.secrets["snowflake"]["account"],
        "user": st.secrets["snowflake"]["user"],
        "password": st.secrets["snowflake"]["password"],
        "warehouse": st.secrets["snowflake"]["warehouse"],
        "database": st.secrets["snowflake"]["database"],
        "schema": st.secrets["snowflake"]["schema"],
    }).create()

session = get_session()

def format_metric(value, prefix="", suffix="", decimals=0):
    if pd.isna(value):
        return f"{prefix}0{suffix}"
    if decimals > 0:
        return f"{prefix}{value:,.{decimals}f}{suffix}"
    return f"{prefix}{value:,.0f}{suffix}"


@st.cache_data(ttl=600)
def load_data(table_name):
    return session.table(f"{DB}.{SCHEMA}.{table_name}").to_pandas()


@st.cache_data(ttl=600)
def get_last_refresh():
    result = session.sql(
        f"SELECT MAX(DBT_LOADED_AT) AS LAST_REFRESH FROM {DB}.{SCHEMA}.FACT_TRANSACTIONS"
    ).to_pandas()
    ts = result["LAST_REFRESH"].iloc[0]
    if ts is not None:
        return pd.Timestamp(ts).strftime("%Y-%m-%d %H:%M:%S UTC")
    return "Unknown"


def render_header():
    last_refresh = get_last_refresh()
    st.markdown(f"### Fintech Analytics Platform")
    st.caption(f"Real-time transaction intelligence powered by Snowflake + dbt | Data last refreshed: {last_refresh}")


def render_footer():
    st.markdown("---")
    st.caption("Pipeline: Snowflake → dbt → Streamlit | Data refreshed every 6 hours | Built by Cong Vu")


def executive_overview():
    with st.expander("Methodology & Metric Definitions", expanded=False):
        st.markdown("""
| Metric | Definition |
|--------|-----------|
| **Total Transactions** | Count of all transaction records in the selected period |
| **Volume (SGD)** | Sum of all transaction amounts converted to SGD using daily FX rates |
| **Fee Revenue (SGD)** | Total platform fees charged, converted to SGD |
| **Success Rate** | Successful transactions / Total transactions x 100 |
| **Cross-Border Txns** | Transactions where source currency != account currency |
""")

    daily_df = load_data("FCT_DAILY_TRANSACTION_SUMMARY")
    daily_df["TRANSACTION_DATE"] = pd.to_datetime(daily_df["TRANSACTION_DATE"])

    st.sidebar.subheader("Filters")
    min_date = daily_df["TRANSACTION_DATE"].min().date()
    max_date = daily_df["TRANSACTION_DATE"].max().date()
    date_range = st.sidebar.date_input(
        "Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date, key="eo_date"
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        daily_df = daily_df[
            (daily_df["TRANSACTION_DATE"].dt.date >= start_date) &
            (daily_df["TRANSACTION_DATE"].dt.date <= end_date)
        ]

    channels = ["All"] + sorted(daily_df["CHANNEL"].dropna().unique().tolist())
    selected_channel = st.sidebar.selectbox("Channel", channels, key="eo_channel")
    currencies = ["All"] + sorted(daily_df["TRANSACTION_CURRENCY"].dropna().unique().tolist())
    selected_currency = st.sidebar.selectbox("Currency", currencies, key="eo_currency")

    if selected_channel != "All":
        daily_df = daily_df[daily_df["CHANNEL"] == selected_channel]
    if selected_currency != "All":
        daily_df = daily_df[daily_df["TRANSACTION_CURRENCY"] == selected_currency]

    total_txns = int(daily_df["TRANSACTION_COUNT"].sum())
    total_amount_sgd = float(daily_df["TOTAL_TRANSACTION_AMOUNT_SGD"].sum())
    total_fee_sgd = float(daily_df["TOTAL_FEE_AMOUNT_SGD"].sum())
    success_count = int(daily_df["SUCCESSFUL_TRANSACTION_COUNT"].sum())
    failed_count = int(daily_df["FAILED_TRANSACTION_COUNT"].sum())
    cross_border_count = int(daily_df["CROSS_BORDER_TRANSACTION_COUNT"].sum())
    success_rate = (success_count / total_txns * 100) if total_txns > 0 else 0

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Total Transactions", format_metric(total_txns))
    k2.metric("Volume (SGD)", format_metric(total_amount_sgd, prefix="$", decimals=2))
    k3.metric("Fee Revenue (SGD)", format_metric(total_fee_sgd, prefix="$", decimals=2))
    k4.metric("Success Rate", format_metric(success_rate, suffix="%", decimals=1))
    k5.metric("Failed Transactions", format_metric(failed_count))
    k6.metric("Cross-Border Txns", format_metric(cross_border_count))

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["Trends", "Composition", "Geography"])

    with tab1:
        daily_agg = daily_df.groupby("TRANSACTION_DATE").agg(
            TRANSACTION_COUNT=("TRANSACTION_COUNT", "sum"),
            TOTAL_TRANSACTION_AMOUNT_SGD=("TOTAL_TRANSACTION_AMOUNT_SGD", "sum"),
        ).reset_index().sort_values("TRANSACTION_DATE").set_index("TRANSACTION_DATE")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Daily Transaction Count")
            st.area_chart(daily_agg["TRANSACTION_COUNT"])
        with col2:
            st.subheader("Daily Transaction Volume (SGD)")
            st.area_chart(daily_agg["TOTAL_TRANSACTION_AMOUNT_SGD"])

    with tab2:
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("Transaction Status Breakdown")
            status_df = daily_df.groupby("TRANSACTION_STATUS")["TRANSACTION_COUNT"].sum().reset_index()
            st.bar_chart(status_df, x="TRANSACTION_STATUS", y="TRANSACTION_COUNT")

        with col4:
            st.subheader("Transaction Channel Breakdown")
            channel_df = daily_df.groupby("CHANNEL")["TRANSACTION_COUNT"].sum().reset_index()
            st.bar_chart(channel_df, x="CHANNEL", y="TRANSACTION_COUNT")

        st.subheader("Currency Mix")
        curr_df = daily_df.groupby("TRANSACTION_CURRENCY")["TOTAL_TRANSACTION_AMOUNT_SGD"].sum().reset_index()
        st.bar_chart(curr_df, x="TRANSACTION_CURRENCY", y="TOTAL_TRANSACTION_AMOUNT_SGD")

    with tab3:
        st.subheader("Cross-Border vs Domestic Transactions")
        cb_count = int(daily_df["CROSS_BORDER_TRANSACTION_COUNT"].sum())
        domestic_count = total_txns - cb_count
        geo_df = pd.DataFrame({"Type": ["Cross-Border", "Domestic"], "Count": [cb_count, domestic_count]})
        st.bar_chart(geo_df, x="Type", y="Count")


def customer_intelligence():
    with st.expander("Methodology & Metric Definitions", expanded=False):
        st.markdown("""
| Metric | Definition |
|--------|-----------|
| **Total Customers** | Distinct customers in DIM_CUSTOMERS matching current filters |
| **Avg Spend (SGD)** | Mean of total_spend_sgd across all customers |
| **Avg Txns/Customer** | Mean transaction count per customer |
| **KYC Verified Rate** | Customers with kyc_is_verified = TRUE / Total customers x 100 |
| **Avg Active Days** | Mean number of distinct days a customer transacted |
""")

    cust_df = load_data("DIM_CUSTOMERS")
    cust_txn_df = load_data("FCT_CUSTOMER_TRANSACTION_SUMMARY")
    merged_df = cust_txn_df.merge(cust_df, on="CUSTOMER_ID", how="left")

    st.sidebar.subheader("Filters")
    segments = ["All"] + sorted(cust_df["CUSTOMER_SEGMENT"].dropna().unique().tolist())
    selected_segment = st.sidebar.selectbox("Customer Segment", segments, key="ci_segment")
    kyc_options = ["All"] + sorted(cust_df["KYC_STATUS"].dropna().unique().tolist())
    selected_kyc = st.sidebar.selectbox("KYC Status", kyc_options, key="ci_kyc")

    if selected_segment != "All":
        merged_df = merged_df[merged_df["CUSTOMER_SEGMENT"] == selected_segment]
        cust_df = cust_df[cust_df["CUSTOMER_SEGMENT"] == selected_segment]
    if selected_kyc != "All":
        merged_df = merged_df[merged_df["KYC_STATUS"] == selected_kyc]
        cust_df = cust_df[cust_df["KYC_STATUS"] == selected_kyc]

    total_customers = cust_df["CUSTOMER_ID"].nunique()
    avg_spend = float(merged_df["TOTAL_SPEND_SGD"].mean()) if len(merged_df) > 0 else 0
    avg_txns = float(merged_df["TOTAL_TRANSACTIONS"].mean()) if len(merged_df) > 0 else 0
    verified_count = int(cust_df["KYC_IS_VERIFIED"].astype(int).sum())
    verified_rate = (verified_count / len(cust_df) * 100) if len(cust_df) > 0 else 0
    avg_active_days = float(merged_df["ACTIVE_TRANSACTION_DAYS"].mean()) if len(merged_df) > 0 else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Customers", format_metric(total_customers))
    k2.metric("Avg Spend (SGD)", format_metric(avg_spend, prefix="$", decimals=2))
    k3.metric("Avg Txns/Customer", format_metric(avg_txns, decimals=1))
    k4.metric("KYC Verified Rate", format_metric(verified_rate, suffix="%", decimals=1))
    k5.metric("Avg Active Days", format_metric(avg_active_days, decimals=1))

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["Segmentation", "Value Analysis", "Cohorts"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Customer Segment Distribution")
            seg_df = cust_df.groupby("CUSTOMER_SEGMENT").size().reset_index(name="COUNT")
            st.bar_chart(seg_df, x="CUSTOMER_SEGMENT", y="COUNT")

        with col2:
            st.subheader("KYC Status Distribution")
            kyc_df = cust_df.groupby("KYC_STATUS").size().reset_index(name="COUNT")
            st.bar_chart(kyc_df, x="KYC_STATUS", y="COUNT")

        st.subheader("Preferred Channel Distribution")
        ch_df = merged_df.groupby("PREFERRED_CHANNEL").size().reset_index(name="COUNT")
        st.bar_chart(ch_df, x="PREFERRED_CHANNEL", y="COUNT")

    with tab2:
        st.subheader("Total Spend by Customer Segment")
        spend_seg = merged_df.groupby("CUSTOMER_SEGMENT")["TOTAL_SPEND_SGD"].sum().reset_index()
        st.bar_chart(spend_seg, x="CUSTOMER_SEGMENT", y="TOTAL_SPEND_SGD")

        st.subheader("Top 10 Customers by Spend")
        top10 = merged_df.nlargest(10, "TOTAL_SPEND_SGD")[
            ["CUSTOMER_ID", "CUSTOMER_NAME", "CUSTOMER_SEGMENT", "TOTAL_SPEND_SGD", "TOTAL_TRANSACTIONS"]
        ].copy()
        top10["TOTAL_SPEND_SGD"] = top10["TOTAL_SPEND_SGD"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(top10, use_container_width=True, hide_index=True)

        st.subheader("Transactions vs Spend by Segment")
        scatter_df = merged_df.groupby("CUSTOMER_SEGMENT").agg(
            AVG_TRANSACTIONS=("TOTAL_TRANSACTIONS", "mean"),
            AVG_SPEND_SGD=("TOTAL_SPEND_SGD", "mean")
        ).reset_index()
        st.dataframe(scatter_df, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Customer Signup Cohort Trend")
        cust_df_copy = cust_df.copy()
        cust_df_copy["SIGNUP_MONTH"] = pd.to_datetime(cust_df_copy["SIGNUP_MONTH"])
        cohort_df = cust_df_copy.groupby("SIGNUP_MONTH").size().reset_index(name="NEW_CUSTOMERS")
        cohort_df = cohort_df.sort_values("SIGNUP_MONTH").set_index("SIGNUP_MONTH")
        st.bar_chart(cohort_df["NEW_CUSTOMERS"])


def transaction_operations():
    with st.expander("Methodology & Metric Definitions", expanded=False):
        st.markdown("""
| Metric | Definition |
|--------|-----------|
| **Success Rate** | Transactions with is_successful = TRUE / Total x 100 |
| **Failure Rate** | Transactions with is_failed = TRUE / Total x 100 |
| **Pending Txns** | Transactions with is_pending = TRUE |
| **Cross-Border Failed** | Failed transactions where is_cross_border = TRUE |
""")

    txn_df = load_data("FACT_TRANSACTIONS")
    daily_df = load_data("FCT_DAILY_TRANSACTION_SUMMARY")
    
import pandas as pd
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Fintech Analytics Dashboard", layout="wide")

session = get_active_session()

DB = "FINTECH_ANALYTICS"
SCHEMA = "RAW_MARTS"


def format_metric(value, prefix="", suffix="", decimals=0):
    if pd.isna(value):
        return f"{prefix}0{suffix}"
    if decimals > 0:
        return f"{prefix}{value:,.{decimals}f}{suffix}"
    return f"{prefix}{value:,.0f}{suffix}"


@st.cache_data(ttl=600)
def load_data(table_name):
    return session.table(f"{DB}.{SCHEMA}.{table_name}").to_pandas()


@st.cache_data(ttl=600)
def get_last_refresh():
    result = session.sql(
        f"SELECT MAX(DBT_LOADED_AT) AS LAST_REFRESH FROM {DB}.{SCHEMA}.FACT_TRANSACTIONS"
    ).to_pandas()
    ts = result["LAST_REFRESH"].iloc[0]
    if ts is not None:
        return pd.Timestamp(ts).strftime("%Y-%m-%d %H:%M:%S UTC")
    return "Unknown"


MONTH_NAMES = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
               7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}


def render_header():
    last_refresh = get_last_refresh()
    st.markdown("### Fintech Analytics Platform")
    st.caption(f"Real-time transaction intelligence powered by Snowflake + dbt | Data last refreshed: {last_refresh}")


def render_footer():
    st.markdown("---")
    st.caption("Pipeline: Snowflake → dbt → Streamlit | Data refreshed every 6 hours | Built by Cong Vu")


def executive_overview():
    with st.expander("Methodology & Metric Definitions", expanded=False):
        st.markdown("""
| Metric | Definition |
|--------|-----------|
| **Total Transactions** | Count of all transaction records in the selected period |
| **Success Rate** | Successful transactions / Total transactions x 100 (2 decimal places) |
| **Volume (SGD)** | Sum of all transaction amounts converted to SGD using daily FX rates |
| **Fee Revenue (SGD)** | Total platform fees charged, converted to SGD |
| **Cross-Border Txns** | Transactions where source currency != account currency |
""")

    daily_df = load_data("FCT_DAILY_TRANSACTION_SUMMARY")
    daily_df["TRANSACTION_DATE"] = pd.to_datetime(daily_df["TRANSACTION_DATE"])
    daily_df["YEAR"] = daily_df["TRANSACTION_DATE"].dt.year
    daily_df["MONTH"] = daily_df["TRANSACTION_DATE"].dt.month

    st.sidebar.subheader("Filters")
    years = sorted(daily_df["YEAR"].unique().tolist())
    selected_year = st.sidebar.selectbox("Year", ["All"] + [str(y) for y in years], key="eo_year")
    months_available = sorted(daily_df["MONTH"].unique().tolist())
    month_options = ["All"] + [MONTH_NAMES[m] for m in months_available]
    selected_month = st.sidebar.selectbox("Month", month_options, key="eo_month")
    channels = ["All"] + sorted(daily_df["CHANNEL"].dropna().unique().tolist())
    selected_channel = st.sidebar.selectbox("Channel", channels, key="eo_channel")
    currencies = ["All"] + sorted(daily_df["TRANSACTION_CURRENCY"].dropna().unique().tolist())
    selected_currency = st.sidebar.selectbox("Currency", currencies, key="eo_currency")

    filtered_df = daily_df.copy()
    if selected_year != "All":
        filtered_df = filtered_df[filtered_df["YEAR"] == int(selected_year)]
    if selected_month != "All":
        month_num = [k for k, v in MONTH_NAMES.items() if v == selected_month][0]
        filtered_df = filtered_df[filtered_df["MONTH"] == month_num]
    if selected_channel != "All":
        filtered_df = filtered_df[filtered_df["CHANNEL"] == selected_channel]
    if selected_currency != "All":
        filtered_df = filtered_df[filtered_df["TRANSACTION_CURRENCY"] == selected_currency]

    total_txns = int(filtered_df["TRANSACTION_COUNT"].sum())
    total_amount_sgd = float(filtered_df["TOTAL_TRANSACTION_AMOUNT_SGD"].sum())
    total_fee_sgd = float(filtered_df["TOTAL_FEE_AMOUNT_SGD"].sum())
    success_count = int(filtered_df["SUCCESSFUL_TRANSACTION_COUNT"].sum())
    failed_count = int(filtered_df["FAILED_TRANSACTION_COUNT"].sum())
    cross_border_count = int(filtered_df["CROSS_BORDER_TRANSACTION_COUNT"].sum())
    success_rate = (success_count / total_txns * 100) if total_txns > 0 else 0

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Total Transactions", format_metric(total_txns))
    k2.metric("Volume (SGD)", format_metric(total_amount_sgd, prefix="$", decimals=2))
    k3.metric("Fee Revenue (SGD)", format_metric(total_fee_sgd, prefix="$", decimals=2))
    k4.metric("Success Rate", format_metric(success_rate, suffix="%", decimals=2))
    k5.metric("Failed Transactions", format_metric(failed_count))
    k6.metric("Cross-Border Txns", format_metric(cross_border_count))

    st.markdown("---")
    st.subheader("Monthly Summary")
    monthly_df = filtered_df.groupby(["YEAR", "MONTH"]).agg(
        TOTAL_TRANSACTIONS=("TRANSACTION_COUNT", "sum"),
        SUCCESSFUL=("SUCCESSFUL_TRANSACTION_COUNT", "sum"),
        VOLUME_SGD=("TOTAL_TRANSACTION_AMOUNT_SGD", "sum"),
        FEE_REVENUE_SGD=("TOTAL_FEE_AMOUNT_SGD", "sum"),
    ).reset_index()
    monthly_df["SUCCESS_RATE"] = (monthly_df["SUCCESSFUL"] / monthly_df["TOTAL_TRANSACTIONS"] * 100).round(2)
    monthly_df["PERIOD"] = monthly_df["MONTH"].map(MONTH_NAMES) + " " + monthly_df["YEAR"].astype(str)
    display_monthly = monthly_df[["PERIOD", "TOTAL_TRANSACTIONS", "SUCCESS_RATE", "VOLUME_SGD", "FEE_REVENUE_SGD"]].copy()
    display_monthly.columns = ["Period", "Total Transactions", "Success Rate (%)", "Volume (SGD)", "Fee Revenue (SGD)"]
    display_monthly["Volume (SGD)"] = display_monthly["Volume (SGD)"].apply(lambda x: f"${x:,.2f}")
    display_monthly["Fee Revenue (SGD)"] = display_monthly["Fee Revenue (SGD)"].apply(lambda x: f"${x:,.2f}")
    display_monthly["Success Rate (%)"] = display_monthly["Success Rate (%)"].apply(lambda x: f"{x:.2f}%")
    st.dataframe(display_monthly, use_container_width=True, hide_index=True)

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["Trends", "Composition", "Geography"])

    with tab1:
        daily_agg = filtered_df.groupby("TRANSACTION_DATE").agg(
            TOTAL_TRANSACTION_AMOUNT_SGD=("TOTAL_TRANSACTION_AMOUNT_SGD", "sum"),
            SUCCESS_NUM=("SUCCESSFUL_TRANSACTION_COUNT", "sum"),
            TOTAL_NUM=("TRANSACTION_COUNT", "sum"),
        ).reset_index().sort_values("TRANSACTION_DATE")
        daily_agg["DAILY_SUCCESS_RATE"] = (daily_agg["SUCCESS_NUM"] / daily_agg["TOTAL_NUM"] * 100).round(2)
        daily_agg = daily_agg.set_index("TRANSACTION_DATE")

        st.subheader("Daily Transaction Volume (SGD)")
        st.area_chart(daily_agg[["TOTAL_TRANSACTION_AMOUNT_SGD"]].rename(columns={"TOTAL_TRANSACTION_AMOUNT_SGD": "Volume (SGD)"}))

    with tab2:
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("Transaction Status Breakdown")
            status_df = filtered_df.groupby("TRANSACTION_STATUS")["TRANSACTION_COUNT"].sum().reset_index()
            status_df.columns = ["Transaction Status", "Number of Transactions"]
            st.bar_chart(status_df, x="Transaction Status", y="Number of Transactions")
        with col4:
            st.subheader("Transaction Channel Breakdown")
            channel_df = filtered_df.groupby("CHANNEL")["TRANSACTION_COUNT"].sum().reset_index()
            channel_df.columns = ["Channel", "Number of Transactions"]
            st.bar_chart(channel_df, x="Channel", y="Number of Transactions")

        st.subheader("Currency Mix")
        curr_df = filtered_df.groupby("TRANSACTION_CURRENCY")["TOTAL_TRANSACTION_AMOUNT_SGD"].sum().reset_index()
        curr_df.columns = ["Currency", "Total Volume (SGD)"]
        st.bar_chart(curr_df, x="Currency", y="Total Volume (SGD)")

    with tab3:
        st.subheader("Cross-Border vs Domestic Transactions")
        cb_count = int(filtered_df["CROSS_BORDER_TRANSACTION_COUNT"].sum())
        domestic_count = total_txns - cb_count
        geo_df = pd.DataFrame({"Transaction Type": ["Cross-Border", "Domestic"], "Number of Transactions": [cb_count, domestic_count]})
        st.bar_chart(geo_df, x="Transaction Type", y="Number of Transactions")


def customer_intelligence():
    with st.expander("Methodology & Metric Definitions", expanded=False):
        st.markdown("""
| Metric | Definition |
|--------|-----------|
| **Total Customers** | Distinct customers in DIM_CUSTOMERS matching current filters |
| **Avg Spend (SGD)** | Mean of total_spend_sgd across all customers |
| **Avg Txns/Customer** | Mean transaction count per customer |
| **KYC Verified Rate** | Customers with kyc_is_verified = TRUE / Total customers x 100 |
| **Avg Active Days** | Mean number of distinct days a customer transacted |
""")

    cust_df = load_data("DIM_CUSTOMERS")
    cust_txn_df = load_data("FCT_CUSTOMER_TRANSACTION_SUMMARY")
    merged_df = cust_txn_df.merge(cust_df, on="CUSTOMER_ID", how="left")

    merged_df["FIRST_TRANSACTION_DATE"] = pd.to_datetime(merged_df["FIRST_TRANSACTION_DATE"])
    merged_df["YEAR"] = merged_df["FIRST_TRANSACTION_DATE"].dt.year
    merged_df["MONTH"] = merged_df["FIRST_TRANSACTION_DATE"].dt.month

    st.sidebar.subheader("Filters")
    segments = ["All"] + sorted(cust_df["CUSTOMER_SEGMENT"].dropna().unique().tolist())
    selected_segment = st.sidebar.selectbox("Customer Segment", segments, key="ci_segment")
    kyc_options = ["All"] + sorted(cust_df["KYC_STATUS"].dropna().unique().tolist())
    selected_kyc = st.sidebar.selectbox("KYC Status", kyc_options, key="ci_kyc")
    countries = ["All"] + sorted(cust_df["COUNTRY"].dropna().unique().tolist())
    selected_country = st.sidebar.selectbox("Country", countries, key="ci_country")

    if selected_segment != "All":
        merged_df = merged_df[merged_df["CUSTOMER_SEGMENT"] == selected_segment]
        cust_df = cust_df[cust_df["CUSTOMER_SEGMENT"] == selected_segment]
    if selected_kyc != "All":
        merged_df = merged_df[merged_df["KYC_STATUS"] == selected_kyc]
        cust_df = cust_df[cust_df["KYC_STATUS"] == selected_kyc]
    if selected_country != "All":
        merged_df = merged_df[merged_df["COUNTRY"] == selected_country]
        cust_df = cust_df[cust_df["COUNTRY"] == selected_country]

    total_customers = cust_df["CUSTOMER_ID"].nunique()
    avg_spend = float(merged_df["TOTAL_SPEND_SGD"].mean()) if len(merged_df) > 0 else 0
    avg_txns = float(merged_df["TOTAL_TRANSACTIONS"].mean()) if len(merged_df) > 0 else 0
    verified_count = int(cust_df["KYC_IS_VERIFIED"].astype(int).sum())
    verified_rate = (verified_count / len(cust_df) * 100) if len(cust_df) > 0 else 0
    avg_active_days = float(merged_df["ACTIVE_TRANSACTION_DAYS"].mean()) if len(merged_df) > 0 else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Customers", format_metric(total_customers))
    k2.metric("Avg Spend (SGD)", format_metric(avg_spend, prefix="$", decimals=2))
    k3.metric("Avg Txns/Customer", format_metric(avg_txns, decimals=1))
    k4.metric("KYC Verified Rate", format_metric(verified_rate, suffix="%", decimals=2))
    k5.metric("Avg Active Days", format_metric(avg_active_days, decimals=1))

    st.markdown("---")
    st.subheader("Customer Summary by Segment")
    seg_summary = merged_df.groupby("CUSTOMER_SEGMENT").agg(
        TOTAL_CUSTOMERS=("CUSTOMER_ID", "nunique"),
        AVG_SPEND_SGD=("TOTAL_SPEND_SGD", "mean"),
        AVG_TRANSACTIONS=("TOTAL_TRANSACTIONS", "mean"),
        TOTAL_SPEND_SGD=("TOTAL_SPEND_SGD", "sum"),
    ).reset_index()
    seg_summary["KYC_RATE"] = merged_df.groupby("CUSTOMER_SEGMENT")["KYC_IS_VERIFIED"].apply(
        lambda x: (x.astype(int).sum() / len(x) * 100)
    ).values
    display_seg = seg_summary.copy()
    display_seg.columns = ["Segment", "Total Customers", "Avg Spend (SGD)", "Avg Transactions", "Total Spend (SGD)", "KYC Verified Rate (%)"]
    display_seg["Avg Spend (SGD)"] = display_seg["Avg Spend (SGD)"].apply(lambda x: f"${x:,.2f}")
    display_seg["Total Spend (SGD)"] = display_seg["Total Spend (SGD)"].apply(lambda x: f"${x:,.2f}")
    display_seg["Avg Transactions"] = display_seg["Avg Transactions"].apply(lambda x: f"{x:.1f}")
    display_seg["KYC Verified Rate (%)"] = display_seg["KYC Verified Rate (%)"].apply(lambda x: f"{x:.2f}%")
    st.dataframe(display_seg, use_container_width=True, hide_index=True)

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["Segmentation", "Value Analysis", "Cohorts"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Customer Segment Distribution")
            seg_df = cust_df.groupby("CUSTOMER_SEGMENT").size().reset_index(name="COUNT")
            seg_df.columns = ["Customer Segment", "Number of Customers"]
            st.bar_chart(seg_df, x="Customer Segment", y="Number of Customers")
        with col2:
            st.subheader("KYC Status Distribution")
            kyc_df = cust_df.groupby("KYC_STATUS").size().reset_index(name="COUNT")
            kyc_df.columns = ["KYC Status", "Number of Customers"]
            st.bar_chart(kyc_df, x="KYC Status", y="Number of Customers")

        st.subheader("Preferred Channel Distribution")
        ch_df = merged_df.groupby("PREFERRED_CHANNEL").size().reset_index(name="COUNT")
        ch_df.columns = ["Preferred Channel", "Number of Customers"]
        st.bar_chart(ch_df, x="Preferred Channel", y="Number of Customers")

    with tab2:
        st.subheader("Total Spend by Customer Segment")
        spend_seg = merged_df.groupby("CUSTOMER_SEGMENT")["TOTAL_SPEND_SGD"].sum().reset_index()
        spend_seg.columns = ["Customer Segment", "Total Spend (SGD)"]
        st.bar_chart(spend_seg, x="Customer Segment", y="Total Spend (SGD)")

        st.subheader("Top 10 Customers by Spend")
        top10 = merged_df.nlargest(10, "TOTAL_SPEND_SGD")[
            ["CUSTOMER_ID", "CUSTOMER_NAME", "CUSTOMER_SEGMENT", "COUNTRY", "TOTAL_SPEND_SGD", "TOTAL_TRANSACTIONS"]
        ].copy()
        top10["TOTAL_SPEND_SGD"] = top10["TOTAL_SPEND_SGD"].apply(lambda x: f"${x:,.2f}")
        top10.columns = ["Customer ID", "Name", "Segment", "Country", "Total Spend (SGD)", "Transactions"]
        st.dataframe(top10, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Customer Activity Summary")
        activity_df = merged_df.groupby("CUSTOMER_SEGMENT").agg(
            AVG_ACTIVE_DAYS=("ACTIVE_TRANSACTION_DAYS", "mean"),
            AVG_CROSS_BORDER=("CROSS_BORDER_TRANSACTIONS", "mean"),
            TOTAL_CUSTOMERS=("CUSTOMER_ID", "nunique"),
        ).reset_index()
        activity_df.columns = ["Segment", "Avg Active Days", "Avg Cross-Border Txns", "Total Customers"]
        activity_df["Avg Active Days"] = activity_df["Avg Active Days"].apply(lambda x: f"{x:.1f}")
        activity_df["Avg Cross-Border Txns"] = activity_df["Avg Cross-Border Txns"].apply(lambda x: f"{x:.1f}")
        st.dataframe(activity_df, use_container_width=True, hide_index=True)

        st.subheader("Spend Distribution by Country")
        country_spend = merged_df.groupby("COUNTRY")["TOTAL_SPEND_SGD"].sum().reset_index()
        country_spend.columns = ["Country", "Total Spend (SGD)"]
        st.bar_chart(country_spend, x="Country", y="Total Spend (SGD)")


def transaction_operations():
    with st.expander("Methodology & Metric Definitions", expanded=False):
        st.markdown("""
| Metric | Definition |
|--------|-----------|
| **Success Rate** | Transactions with is_successful = TRUE / Total x 100 |
| **Failure Rate** | Transactions with is_failed = TRUE / Total x 100 |
| **Pending Txns** | Transactions with is_pending = TRUE |
| **Cross-Border Failed** | Failed transactions where is_cross_border = TRUE |
""")

    txn_df = load_data("FACT_TRANSACTIONS")
    daily_df = load_data("FCT_DAILY_TRANSACTION_SUMMARY")

    txn_df["TRANSACTION_DATE"] = pd.to_datetime(txn_df["TRANSACTION_DATE"])
    txn_df["YEAR"] = txn_df["TRANSACTION_DATE"].dt.year
    txn_df["MONTH"] = txn_df["TRANSACTION_DATE"].dt.month

    st.sidebar.subheader("Filters")
    years = sorted(txn_df["YEAR"].unique().tolist())
    selected_year = st.sidebar.selectbox("Year", ["All"] + [str(y) for y in years], key="to_year")
    months_available = sorted(txn_df["MONTH"].unique().tolist())
    month_options = ["All"] + [MONTH_NAMES[m] for m in months_available]
    selected_month = st.sidebar.selectbox("Month", month_options, key="to_month")
    channels = ["All"] + sorted(txn_df["CHANNEL"].dropna().unique().tolist())
    selected_channel = st.sidebar.selectbox("Channel", channels, key="to_channel")
    statuses = ["All"] + sorted(txn_df["TRANSACTION_STATUS"].dropna().unique().tolist())
    selected_status = st.sidebar.selectbox("Status", statuses, key="to_status")

    if selected_year != "All":
        txn_df = txn_df[txn_df["YEAR"] == int(selected_year)]
    if selected_month != "All":
        month_num = [k for k, v in MONTH_NAMES.items() if v == selected_month][0]
        txn_df = txn_df[txn_df["MONTH"] == month_num]
    if selected_channel != "All":
        txn_df = txn_df[txn_df["CHANNEL"] == selected_channel]
        daily_df = daily_df[daily_df["CHANNEL"] == selected_channel]
    if selected_status != "All":
        txn_df = txn_df[txn_df["TRANSACTION_STATUS"] == selected_status]
        daily_df = daily_df[daily_df["TRANSACTION_STATUS"] == selected_status]

    total = len(txn_df)
    success_count = int(txn_df["IS_SUCCESSFUL"].astype(int).sum())
    failed_count = int(txn_df["IS_FAILED"].astype(int).sum())
    pending_count = int(txn_df["IS_PENDING"].astype(int).sum())
    success_rate = (success_count / total * 100) if total > 0 else 0
    failure_rate = (failed_count / total * 100) if total > 0 else 0
    failed_df = txn_df[txn_df["IS_FAILED"] == True].copy()
    cb_failed = int(failed_df[failed_df["IS_CROSS_BORDER"] == True].shape[0])

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Success Rate", format_metric(success_rate, suffix="%", decimals=2))
    k2.metric("Failure Rate", format_metric(failure_rate, suffix="%", decimals=2))
    k3.metric("Pending Txns", format_metric(pending_count))
    k4.metric("Total Failed", format_metric(failed_count))
    k5.metric("Cross-Border Failed", format_metric(cb_failed))

    st.markdown("---")
    st.subheader("Monthly Operations Summary")
    monthly_ops = txn_df.groupby(["YEAR", "MONTH"]).agg(
        TOTAL=("TRANSACTION_ID", "count"),
        SUCCESS=("IS_SUCCESSFUL", lambda x: int(x.astype(int).sum())),
        FAILED=("IS_FAILED", lambda x: int(x.astype(int).sum())),
        PENDING=("IS_PENDING", lambda x: int(x.astype(int).sum())),
    ).reset_index()
    monthly_ops["SUCCESS_RATE"] = (monthly_ops["SUCCESS"] / monthly_ops["TOTAL"] * 100).round(2)
    monthly_ops["FAILURE_RATE"] = (monthly_ops["FAILED"] / monthly_ops["TOTAL"] * 100).round(2)
    monthly_ops["PERIOD"] = monthly_ops["MONTH"].map(MONTH_NAMES) + " " + monthly_ops["YEAR"].astype(str)
    display_ops = monthly_ops[["PERIOD", "TOTAL", "SUCCESS_RATE", "FAILURE_RATE", "FAILED", "PENDING"]].copy()
    display_ops.columns = ["Period", "Total Transactions", "Success Rate (%)", "Failure Rate (%)", "Failed Count", "Pending Count"]
    display_ops["Success Rate (%)"] = display_ops["Success Rate (%)"].apply(lambda x: f"{x:.2f}%")
    display_ops["Failure Rate (%)"] = display_ops["Failure Rate (%)"].apply(lambda x: f"{x:.2f}%")
    st.dataframe(display_ops, use_container_width=True, hide_index=True)

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["Failures", "Channels & Types", "Detail Table"])

    with tab1:
        st.subheader("Failure Reason Breakdown")
        if len(failed_df) > 0:
            reason_df = failed_df.groupby("FAILURE_REASON").size().reset_index(name="COUNT")
            reason_df.columns = ["Failure Reason", "Number of Failures"]
            st.bar_chart(reason_df, x="Failure Reason", y="Number of Failures")
        else:
            st.info("No failed transactions in current filter selection.")
        

    with tab2:
        st.subheader("Transaction Status by Channel")
        ch_status = txn_df.groupby(["CHANNEL", "TRANSACTION_STATUS"]).size().reset_index(name="COUNT")
        pivot_status = ch_status.pivot(index="CHANNEL", columns="TRANSACTION_STATUS", values="COUNT").fillna(0)
        st.bar_chart(pivot_status)

        st.subheader("Transaction Type Breakdown")
        type_df = txn_df.groupby("TRANSACTION_TYPE").size().reset_index(name="COUNT")
        type_df.columns = ["Transaction Type", "Number of Transactions"]
        st.bar_chart(type_df, x="Transaction Type", y="Number of Transactions")

        st.subheader("Channel x Transaction Type")
        heatmap_df = txn_df.groupby(["CHANNEL", "TRANSACTION_TYPE"]).size().reset_index(name="COUNT")
        pivot_heat = heatmap_df.pivot(index="CHANNEL", columns="TRANSACTION_TYPE", values="COUNT").fillna(0).astype(int)
        st.dataframe(pivot_heat, use_container_width=True)

    with tab3:
        st.subheader("Failed Transaction Details")
        if len(failed_df) > 0:
            display_df = failed_df[["TRANSACTION_ID", "CUSTOMER_ID", "TRANSACTION_DATE", "CHANNEL",
                                    "TRANSACTION_TYPE", "FAILURE_REASON", "TRANSACTION_AMOUNT_SGD"]].copy()
            display_df = display_df.sort_values("TRANSACTION_DATE", ascending=False).head(50)
            display_df["TRANSACTION_AMOUNT_SGD"] = display_df["TRANSACTION_AMOUNT_SGD"].apply(lambda x: f"${x:,.2f}")
            display_df.columns = ["Transaction ID", "Customer ID", "Date", "Channel", "Type", "Failure Reason", "Amount (SGD)"]
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No failed transactions to display.")


st.sidebar.title("Fintech Analytics")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigate", ["Executive Overview", "Customer Intelligence", "Transaction Operations"])
st.sidebar.markdown("---")
st.sidebar.caption("Built with Snowflake + dbt + Streamlit")

render_header()

if page == "Executive Overview":
    executive_overview()
elif page == "Customer Intelligence":
    customer_intelligence()
elif page == "Transaction Operations":
    transaction_operations()

render_footer()
