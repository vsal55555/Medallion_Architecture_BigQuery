import pandas as pd
import pyarrow
import sqlalchemy
import pyodbc
import os
import pyarrow.parquet as pq

from sqlalchemy import create_engine


# ============================================================
# 1. Connect to SQL Server
# ============================================================

engine = create_engine(
    "mssql+pyodbc://username:password@DESKTOP-75UOVBF/Kist_Msia_DB"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
)


# ============================================================
# 2. Test SQL Server connection
# ============================================================

with engine.connect() as connection:
    print("SQL Server connection successful!")


# ============================================================
# 3. SQL Query
# ============================================================

query = """
SELECT *
FROM dbo.moneysend
WHERE DOT >= '2009-07-08 00:00:00.000'
AND DOT < '2015-06-03 00:00:00.000';
"""


# ============================================================
# 4. Extract SQL Server data into Pandas
# ============================================================

df = pd.read_sql(query, engine)

print("\nFirst 5 rows:")
print(df.head())

print("\nPandas data types:")
print(df.dtypes)


# ============================================================
# 5. Convert datetime columns to microsecond precision
# ============================================================

date_columns = [
    "DOT",
    "paidDate",
    "PODDate",
    "confirmDate",
    "lock_dot",
    "local_DOT",
    "cancel_date"
]

for col in date_columns:
    if col in df.columns:
        df[col] = df[col].astype("datetime64[us]")


print("\nData types after datetime conversion:")
print(df[date_columns].dtypes)


# ============================================================
# 6. Create Parquet file
# ============================================================

parquet_file = "moneysend.parquet"

df.to_parquet(
    parquet_file,
    engine="pyarrow",
    index=False
)


# ============================================================
# 7. Check whether Parquet file was created
# ============================================================

print("\nFile created:", os.path.exists(parquet_file))

if os.path.exists(parquet_file):
    file_size = os.path.getsize(parquet_file) / (1024 * 1024)
    print(f"File size: {file_size:.2f} MB")


# ============================================================
# 8. Read Parquet back and verify
# ============================================================

parquet_df = pd.read_parquet(
    parquet_file,
    engine="pyarrow"
)

print("\nParquet data types:")
print(parquet_df.dtypes)


# ============================================================
# 9. Check DOT values
# ============================================================

print("\nFirst 5 DOT values:")
print(parquet_df["DOT"].head())


# ============================================================
# 10. Check actual Parquet schema
# ============================================================

table = pq.read_table(parquet_file)

print("\nParquet schema:")
print(table.schema)