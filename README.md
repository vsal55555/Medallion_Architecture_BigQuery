# Remittance Analytics Platform | Medallion Architecture on BigQuery Sandbox

## Project Overview

This project demonstrates an end-to-end Data Engineering solution for remittance transaction analytics using:

- SQL Server (Source System)
- BigQuery Sandbox (Cloud Data Warehouse)
- Medallion Architecture (Bronze / Silver / Gold)
- Looker Studio (Visualization)
- Data Privacy & PII Masking
- Financial Analytics & Executive Reporting

The objective is to ingest raw remittance transaction data, transform and standardize it, protect sensitive customer information, build business-ready data models, and deliver executive dashboards.

---

# Architecture

```text
SQL Server
    │
    ▼
CSV Export
    │
    ▼
BigQuery Sandbox
    │
    ▼
Bronze Layer
    │
    ▼
raw_remittance_transactions
    │
    ▼
Silver Layer
    │
    ▼
fact_transactions
dim_agent
dim_customer
dim_receiver
    │
    ▼
Gold Layer
    │
    ▼
agent_performance
country_corridor
monthly_summary
commission_summary
executive_kpi
    │
    ▼
Looker Studio
    │
    ▼
Executive Dashboard
Agent Dashboard
Corridor Dashboard
Commission Dashboard
```
