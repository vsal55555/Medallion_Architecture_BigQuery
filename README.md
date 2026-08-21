# Remittance Analytics Platform | Medallion Architecture on BigQuery Sandbox

## Project Overview

Remittance Analytics Platform using BigQuery Sandbox, Medallion Architecture, and Looker Studio.
This project demonstrates an end-to-end Data Engineering solution for remittance transaction analytics using:

- SQL Server (Source System)
- BigQuery Sandbox (Cloud Data Warehouse)
- Medallion Architecture (Bronze / Silver / Gold)
- Looker Studio (Visualization)
- Data Privacy & PII Masking
- Financial Analytics & Executive Reporting

The objective is to ingest raw remittance transaction data, transform and standardize it, protect sensitive customer information, build business-ready data models, and deliver executive dashboards.

---

# Architecture (Simple Flow)

```text
SQL Server
    │
    ▼
Python
    │
    ▼
Parquet Export
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

## Data Architecture

```text
                 SQL Server
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
   Data Extraction       Metadata Extraction
          │                     │
          ▼                     ▼
   transactions.parquet   schema_metadata.json
          │                     │
          └──────────┬──────────┘
                     │
                     ▼
           Cloud Data Platform
```

---

## Architecture Overview

This architecture separates **data extraction** and **metadata extraction** from the source database.

### Data Extraction

The data extraction process retrieves transactional records from SQL Server and stores them in a highly optimized columnar format.

**Output:**

```text
transactions.parquet
```

Benefits:

- Smaller file size
- Faster query performance
- Preserves data types
- Cloud analytics optimized

---

### Metadata Extraction

The metadata extraction process captures schema information directly from the source system.

**Output:**

```text
schema_metadata.json
```

Typical metadata includes:

- Table Name
- Column Names
- Data Types
- Length
- Precision
- Scale
- Nullable Flag

Example:

```json
{
  "table_name": "remittance_transactions",
  "columns": [
    {
      "column_name": "Tranno",
      "data_type": "INT"
    },
    {
      "column_name": "paidAmt",
      "data_type": "MONEY"
    }
  ]
}
```

Benefits:

- Data Catalog Creation
- Data Lineage
- Schema Drift Detection
- Automated Documentation

---

## Parquet Storage Layer

The extracted data is stored as Parquet files.

### Example

```text
data/
└── parquet/
    ├── transactions_2024.parquet
    ├── transactions_2025.parquet
    └── transactions_2026.parquet
```

Advantages:

- Columnar Storage
- Compression
- Schema Preservation
- High Performance Analytics

---

## Metadata Repository

Metadata files are stored alongside the data files.

### Example

```text
metadata/
└── schema_metadata.json
```

This allows:

- Schema Validation
- Data Governance
- Automated Data Dictionary Generation

# Tech Stack

- **SQL Server** - Source Database
- **BigQuery Sandbox** - Cloud Data Warehouse
- **SQL** - Data Transformation & Analytics
- **Looker Studio** - Data Visualization & Dashboarding
- **GitHub** - Version Control & Documentation
- **Medallion Architecture** - Data Modeling Framework

---

# Dataset Description

The source dataset contains remittance transaction data including:

## Transaction Information

- Transaction Number
- Reference Number
- Transaction Date
- Transaction Status
- Transfer Type

## Sender Information

- Customer ID
- Sender Name
- Sender Address
- Phone Number
- Email Address
- Passport Number
- Country

## Receiver Information

- Receiver Name
- Receiver Address
- Phone Number
- Email Address
- Identification Number
- Country

## Agent Information

- Agent ID
- Agent Name
- Branch
- Branch Code

## Financial Information

- Paid Amount
- Received Amount
- Exchange Rate
- Commission
- Service Charges

---

# Medallion Architecture

Medallion Architecture is a data design pattern that organizes data into layers as it moves from raw data to business-ready data.
The three layers are:

```text
Bronze
   ↓
Silver
   ↓
Gold
```

Think of it as:

```text
Raw Data
   ↓
Clean Data
   ↓
Business Data
```

## Bronze Layer(Raw)

- No cleaning.
- No transformations.
- No business rules.

### Purpose

Store raw transaction data exactly as received from the source system.

#### Benefits

- Keeps original data untouched
- Easy recovery if transformations fail
- Provides audit trail

### Dataset

```text
bronze
```

### Table

```text
raw_remittance_transactions
```

### Activities

- Export data from SQL Server
- Upload parquet file into BigQuery Sandbox
- Parquet is a modern analytics file format designed for big data which internally stored column-by-column. This is called Columnar Storage. In contrast with csv, which Stores data row-by-row.
- Preserve original schema and source records
- No transformations applied

### Example Query

```sql
SELECT *
FROM `remittance-realtime-de.bronze.raw_remittance_transactions`
LIMIT 100;
```

---

## Silver Layer (Cleaned)

### Purpose

Clean, standardize, secure, and model data for analytics.

### Dataset

```text
silver
```

### Tables

```text
fact_transactions
dim_agent
dim_customer
dim_receiver
```

---

### Agent Dimension

#### Table

```text
silver.dim_agent
```

#### Transformations

- Removed duplicates
- Standardized text values using UPPER()
- Trimmed unnecessary spaces

#### Columns

- Agent ID
- Agent Name
- Branch Code
- Branch Name

---

### Customer Dimension

#### Table

```text
silver.dim_customer
```

#### Data Privacy Implementation

Sensitive information was masked before exposing to reporting users.

##### Protected Fields

- Sender Phone
- Sender Email
- Sender Passport
- Receiver Phone
- Receiver Email
- Receiver ID

##### Compliance Benefits

- Reduced PII exposure
- Safer analytical environment

##### Phone Number Masking

```text
9801234567
↓
XXXXXXX567
```

##### Email Masking

```text
john.doe@gmail.com
↓
j***@gmail.com
```

##### Passport Masking

```text
AB1234567
↓
*****4567
```

---

### Receiver Dimension

#### Table

```text
silver.dim_receiver
```

#### Protected Fields

- Receiver Phone
- Receiver Mobile
- Receiver Email
- Receiver Identification Number

#### Example

```text
123456789
↓
*****6789
```

---

### Fact Transactions

#### Table

```text
silver.fact_transactions
```

#### Transformations

- Standardized transaction statuses
- Converted numeric values using SAFE_CAST()
- Cleaned textual values
- Created business-ready transaction records

##### Example

```text
Paid
PAID
paid

↓

PAID
```

---

# Gold Layer (Business)

## Purpose

Provide business-ready datasets optimized for analytics and reporting.

### Dataset

```text
gold
```

---

## Agent Performance

### Table

```text
gold.agent_performance
```

### Business Metrics

- Transaction Count
- Total Paid Amount
- Total Received Amount
- Average Transaction Size

### Business Use Case

Identify top-performing agents and branches based on transaction volume.

---

## Country Corridor Analysis

### Table

```text
gold.country_corridor
```

### Business Metrics

- Sender Country
- Receiver Country
- Transaction Count
- Transaction Volume

### Example Corridors

```text
Bahrain → Nepal
Qatar → Nepal
Malaysia → Nepal
```

### Business Use Case

Analyze remittance flow between countries.

---

## Monthly Summary

### Table

```text
gold.monthly_summary
```

### Business Metrics

- Year
- Month
- Transaction Count
- Total Volume
- Average Transaction Size

### Business Use Case

Trend analysis and seasonal remittance behavior.

---

## Commission Summary

### Table

```text
gold.commission_summary
```

### Business Metrics

- IME Commission
- Bank Commission
- Sender

---

## Project Outcomes

Successfully built:

- Cloud Data Warehouse using BigQuery Sandbox
- Medallion Architecture(Bronze, Silver, Gold Layers)
- Data Cleaning & Standardization
- PII Masking
- Financial Analytics and Executive Reporting
- Interactive Looker Studio Dashboards

---

## Future Enhancements

- Automated ingestion using Cloud Functions
- dbt transformations
- Apache Airflow orchestration
- Real-time streaming ingestion
- Data Quality Monitoring
- CI/CD deployment
- Infrastructure as Code (Terraform)

---

## 👨‍💻 Author

**Bishal Shrestha**

Data Engineering Capstone Project

---
