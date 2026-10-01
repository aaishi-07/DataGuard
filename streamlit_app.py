import streamlit as st
import pandas as pd

# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(
    page_title="DataGuard",
    page_icon="🛡️",
    layout="wide"
)

# -----------------------------
# Snowflake connection
# -----------------------------
conn = st.connection("snowflake")
session = conn.session()

# -----------------------------
# Title
# -----------------------------
st.title("🛡️ DataGuard")
st.subheader("Data Quality Monitoring Dashboard")

st.write(
    "Databricks Bronze → Silver → Gold → Snowflake"
)

# -----------------------------
# Load Gold DQ Results
# -----------------------------
dq_query = """
SELECT
    TABLE_NAME,
    LOAD_ID,
    RULE_ID,
    RULE_NAME,
    RULE_SCOPE,
    ROWS_CHECKED,
    ROWS_FAILED
FROM PIPELINE_HEALTH.GOLD.GOLD_DQ_RESULTS
ORDER BY TABLE_NAME, LOAD_ID, RULE_ID
"""

dq_df = session.sql(dq_query).to_pandas()

# -----------------------------
# Load Gold Freshness
# -----------------------------
freshness_query = """
SELECT
    TABLE_NAME,
    HOURS_BEHIND,
    EXPECTED_INTERVAL_HOURS,
    FRESHNESS_STATUS
FROM PIPELINE_HEALTH.GOLD.GOLD_FRESHNESS
ORDER BY TABLE_NAME
"""

freshness_df = session.sql(freshness_query).to_pandas()

# -----------------------------
# Key Metrics
# -----------------------------

total_failed = int(dq_df["ROWS_FAILED"].sum())

orders_failed = int(
    dq_df.loc[
        dq_df["TABLE_NAME"].str.upper() == "ORDERS",
        "ROWS_FAILED"
    ].sum()
)

customers_failed = int(
    dq_df.loc[
        dq_df["TABLE_NAME"].str.upper() == "CUSTOMERS",
        "ROWS_FAILED"
    ].sum()
)

# -----------------------------
# Metric Cards
# -----------------------------

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Bronze Orders",
        "75,000"
    )

with col2:
    st.metric(
        "Silver Orders",
        "74,500"
    )

with col3:
    st.metric(
        "Row-Level Rejects",
        "500"
    )

with col4:
    st.metric(
        "Gold DQ Records",
        "132"
    )

# -----------------------------
# Data Quality Rules
# -----------------------------

st.divider()

st.header("📊 Data Quality Rules")

rule_summary = (
    dq_df
    .groupby(["RULE_ID", "RULE_NAME"], as_index=False)["ROWS_FAILED"]
    .sum()
    .sort_values("RULE_ID")
)

rule_summary = rule_summary.rename(
    columns={"ROWS_FAILED": "FAILED_ROWS"}
)

st.dataframe(
    rule_summary,
    use_container_width=True,
    hide_index=True
)

# -----------------------------
# DQ Chart
# -----------------------------

st.subheader("Failures by Rule")

chart_data = rule_summary.set_index("RULE_ID")["FAILED_ROWS"]

st.bar_chart(chart_data)

# -----------------------------
# Freshness
# -----------------------------

st.divider()

st.header("⏱️ Data Freshness")

for _, row in freshness_df.iterrows():

    table_name = row["TABLE_NAME"]
    hours = row["HOURS_BEHIND"]
    status = row["FRESHNESS_STATUS"]

    if str(status).upper() == "FRESH":
        st.success(
            f"{table_name}: {hours} hours behind — FRESH"
        )
    else:
        st.error(
            f"{table_name}: {hours} hours behind — STALE"
        )

# -----------------------------
# Freshness Table
# -----------------------------

st.dataframe(
    freshness_df,
    use_container_width=True,
    hide_index=True
)

# -----------------------------
# Detailed DQ Results
# -----------------------------

st.divider()

st.header("🔍 Detailed DQ Results")

st.dataframe(
    dq_df,
    use_container_width=True,
    hide_index=True
)

# -----------------------------
# Architecture
# -----------------------------

st.divider()

st.header("🏗️ DataGuard Architecture")

st.write(
    """
    CSV Files
    ↓
    Databricks Bronze
    ↓
    Data Quality Rules R1–R7
    ↓
    Databricks Silver
    ↓
    Gold DQ & Freshness
    ↓
    Snowflake
    ↓
    DataGuard Streamlit Dashboard
    """
)

st.caption(
    "DataGuard — Databricks Data Quality & Snowflake Monitoring"
)