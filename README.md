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

## Bronze Layer

### Purpose

Store raw transaction data exactly as received from the source system.

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
- Upload CSV files into BigQuery Sandbox
- Preserve original schema and source records
- No transformations applied

### Example Query

```sql
SELECT *
FROM `remittance-realtime-de.bronze.raw_remittance_transactions`
LIMIT 100;
```

---

## Silver Layer

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

# Gold Layer

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
