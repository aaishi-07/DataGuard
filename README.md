# Databricks Bronze-Silver-Gold Data Quality Pipeline

## Project Overview

This project implements a **Bronze → Silver → Gold** data engineering pipeline in Databricks using PySpark.

The pipeline processes Orders and Customers data, applies data-quality rules, records rejected data, calculates data freshness, and prepares Gold-layer outputs for migration to Snowflake.

## Architecture

```text
                    ┌──────────────────────┐
                    │     Source Data      │
                    │  Orders + Customers  │
                    │      CSV Files       │
                    └──────────┬───────────┘
                               │
                               ▼
                ┌─────────────────────────────┐
                │       BRONZE LAYER          │
                │     Raw Data Ingestion      │
                │                             │
                │  bronze_orders              │
                │  bronze_customers           │
                │  Manifest / Load Metadata   │
                └─────────────┬───────────────┘
                              │
                     Data Quality Checks
                     R1 ─ R5
                              │
                 ┌────────────┴────────────┐
                 │                         │
                 ▼                         ▼
        Valid Records              Rejected Records
                 │                         │
                 ▼                         ▼
        ┌─────────────────┐       ┌──────────────────┐
        │ SILVER LAYER    │       │ DQ / Rejections  │
        │                 │       │                  │
        │ silver_orders   │       │ R1-R5 rejects    │
        │ Cleaned data    │       │ R6 file checks   │
        │ Deduplicated    │       │ R7 row-count     │
        └────────┬────────┘       └────────┬─────────┘
                 │                         │
                 └────────────┬────────────┘
                              ▼
                 ┌─────────────────────────┐
                 │       GOLD LAYER        │
                 │                         │
                 │ gold_dq_results         │
                 │ gold_freshness          │
                 │                         │
                 │ DQ metrics + monitoring │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │       Snowflake         │
                 │                         │
                 │ GOLD_DQ_RESULTS         │
                 │ GOLD_FRESHNESS          │
                 └─────────────────────────┘
```

## Technologies Used

- Databricks
- Apache Spark / PySpark
- Delta Tables
- CSV
- Snowflake
- GitHub

## Data Sources

The project processes:

- **16 Orders loads**
- **10 Customer loads**

The Orders data includes a Day 14 file with a different column order. The pipeline handles this using the declared schema and column names rather than relying on positional mapping.

Day 15 is used for the zero-row/file-level data-quality case.

# 1. Bronze Layer

The Bronze layer ingests the source data and adds metadata for traceability.

### Bronze metadata

- `_source_file`
- `_ingested_at`
- `_load_id`
- `_row_hash`

### Orders

The Orders Bronze data contains **75,000 rows**.

A load manifest records the logical Orders loads, source paths, row counts, and columns.

### Customers

The project processes 10 Customer loads and includes them in the Bronze load manifest.

# 2. Silver Layer

The Silver layer performs data-quality validation and separates valid data from rejected data.

## Row-Level Data Quality Rules

| Rule | Description | Expected Rejected Rows |
|------|-------------|------------------------:|
| R1 | Null order ID | 0 |
| R2 | Duplicate order ID | 150 |
| R3 | Quantity not numeric | 40 |
| R4 | Unknown customer | 220 |
| R5 | Order timestamp out of range | 90 |

Total row-level rejected records:

```text
0 + 150 + 40 + 220 + 90 = 500
```

Valid Silver Orders:

```text
75,000 - 500 = 74,500
```

Row-level rejected records are stored in:

```text
silver_order_rejections
```

## File-Level Data Quality Rules

| Rule | Description | Expected Result |
|------|-------------|----------------:|
| R6 | Column contract violation | 1 file |
| R7 | Row count compared with expected/median | 1 file |

File-level rejected records are stored in:

```text
silver_file_rejections
```

The project validates R6 on Day 14 and R7 on Day 15.

# 3. Gold Layer

The Gold layer produces summarized data-quality results and freshness information.

## Gold DQ Results

The final Gold DQ table contains **132 rows**.

```text
Orders:
16 loads × 7 rules = 112 rows

Customers:
10 loads × 2 rules = 20 rows

Total:
112 + 20 = 132 rows
```

The table is:

```text
gold_dq_results
```

For row-level Orders rules:

```text
0 + 150 + 40 + 220 + 90 = 500
```

## Freshness Monitoring

The expected refresh interval is **24 hours**.

| Table | Hours Behind | Expected Interval | Status |
|-------|-------------:|------------------:|--------|
| Orders | 0 | 24 | FRESH |
| Customers | 144 | 24 | STALE |

The freshness table is:

```text
gold_freshness
```

Orders freshness is calculated from persisted Silver Orders data so rejected records do not incorrectly make Orders appear more recent.

# 4. Gold Business Questions

### Question 1: Rows rejected per load, rule and day

The pipeline groups Silver rejection records by day, rule, load ID, and reason.

### Question 2: How fresh is each table?

The pipeline calculates:

- `hours_behind`
- `expected_interval_hours`
- `freshness_status`

### Question 3: Which rule fires most?

R4 (Unknown Customer) produces **220 rejected rows** in the project test data. The R4 analysis identifies the invalid customer reference in those rejected records.

# 5. Snowflake Migration

The final Gold outputs are exported from Databricks as CSV files and migrated to Snowflake.

Main outputs:

```text
gold_dq_results
gold_freshness
```

Snowflake validation confirmed that the Gold DQ and freshness outputs were loaded successfully.

# 6. Final Project Results

| Check | Result |
|------|-------:|
| Bronze Orders rows | 75,000 |
| R1 rejected | 0 |
| R2 rejected | 150 |
| R3 rejected | 40 |
| R4 rejected | 220 |
| R5 rejected | 90 |
| Total row rejects | 500 |
| Silver Orders rows | 74,500 |
| R6 file rejection | 1 |
| R7 file rejection | 1 |
| Gold DQ rows | 132 |
| Order row-scope failures | 500 |
| Orders freshness | 0 hours / FRESH |
| Customers freshness | 144 hours / STALE |

# 7. Repository Structure

```text
project/
│
├── 2570002_notebook_bronze_silver_gold (19)(1).py
├── README.md
└── requirements.txt
```

Optional screenshots can be stored in a `screenshots/` folder.

# 8. How to Run

This project is designed to run in **Databricks**.

1. Import the Python notebook into Databricks.
2. Ensure the required source CSV files are available at the configured project paths.
3. Run the notebook from the beginning.
4. Verify the Bronze, Silver, and Gold validation results.
5. Export the required Gold outputs.
6. Load the outputs into Snowflake for final validation.

The notebook should be run as a complete workflow rather than executing isolated cells.

# 9. Requirements

The project uses the Databricks/Spark runtime.

```text
pyspark
```

PySpark is normally provided by the Databricks runtime, so `requirements.txt` is mainly included to document the environment.

## Author

**2570002**

Databricks Data Engineering Project
