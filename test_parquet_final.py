import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pyodbc
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# ============================================================
# CONFIGURATION
# ============================================================

SERVER = r"DESKTOP-75UOVBF"
DATABASE = "Kist_Msia_DB"
DRIVER = "ODBC Driver 17 for SQL Server"

TABLE_SCHEMA = "dbo"
TABLE_NAME = "moneysend"

OUTPUT_FILE = "moneysend.parquet"


# ============================================================
# 1. CHECK ODBC DRIVER
# ============================================================

available_drivers = pyodbc.drivers()

print("Available ODBC drivers:")
print(available_drivers)

if DRIVER not in available_drivers:
    raise RuntimeError(
        f"\n'{DRIVER}' was not found.\n"
        f"Available drivers: {available_drivers}\n"
        "Change DRIVER to an installed SQL Server ODBC driver."
    )


# ============================================================
# 2. CREATE SQL SERVER CONNECTION
#    Windows Authentication
# ============================================================

connection_url = URL.create(
    "mssql+pyodbc",
    query={
        "odbc_connect": (
            f"DRIVER={{{DRIVER}}};"
            f"SERVER={SERVER};"
            f"DATABASE={DATABASE};"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
        )
    },
)

engine = create_engine(connection_url)


# ============================================================
# 3. TEST SQL SERVER CONNECTION
# ============================================================

with engine.connect() as connection:
    print("\nSQL Server connection successful!")


# ============================================================
# 4. GET ORIGINAL SQL SERVER COLUMN TYPES
#
#    This is important for columns where every extracted value
#    is NULL. Pandas cannot determine their original SQL type
#    from an all-NULL result.
# ============================================================

metadata_query = text("""
SELECT
    COLUMN_NAME,
    DATA_TYPE,
    NUMERIC_PRECISION,
    NUMERIC_SCALE,
    ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = :schema_name
  AND TABLE_NAME = :table_name
ORDER BY ORDINAL_POSITION;
""")

with engine.connect() as connection:
    metadata_rows = connection.execute(
        metadata_query,
        {
            "schema_name": TABLE_SCHEMA,
            "table_name": TABLE_NAME,
        },
    ).mappings().all()

if not metadata_rows:
    raise RuntimeError(
        f"Table {TABLE_SCHEMA}.{TABLE_NAME} was not found."
    )

sql_metadata = {
    row["COLUMN_NAME"]: dict(row)
    for row in metadata_rows
}

print(f"\nSQL Server columns found: {len(sql_metadata)}")


# ============================================================
# 5. EXTRACT DATA FROM SQL SERVER
# ============================================================

query = f"""
SELECT 
    Tranno,
    dbo.decryptDb(refno) as refno,
    agentid,
    agentname,
    Branch_code,
    Branch,
    CustomerId,
    SenderName,
    SenderAddress,
    SenderPhoneno,
    senderSalary,
    senderFax,
    SenderCity,
    SenderCountry,
    SenderEmail,
    SenderCompany,
    senderPassport,
    senderVisa,
    ReceiverName,
    ReceiverAddress,
    ReceiverPhone,
    ReceiverFax,
    ReceiverCity,
    ReceiverCountry,
    ReceiverRelation,
    ReceiverIDDescription,
    ReceiverID,
    DOT,
    DOtTime,
    paidAmt,
    paidCType,
    receiveAmt,
    receiveCType,
    ExchangeRate,
    Today_Dollar_rate,
    Dollar_Amt,
    SCharge,
    ReciverMessage,
    TestQuestion,
    TestAnswer,
    amtSenderType,
    SenderBankID,
    SenderBankName,
    SenderBankBranch,
    SenderBankVoucherNo,
    Amt_paid_date,
    paymentType,
    rBankID,
    rBankName,
    rBankBranch,
    rBankACNo,
    rBankAcType,
    otherCharge,
    TransStatus,
    status,
    SEmpID,
    bTno,
    imeCommission,
    bankCommission,
    TotalRoundAmt,
    TransferType,
    paidBy,
    paidDate,
    paidTime,
    courierID,
    PODDate,
    senderCommission,
    receiverCommission,
    approve_by,
    receiveAgentID,
    send_mode,
    confirmDate,
    lock_status,
    lock_dot,
    lock_by,
    local_DOT,
    sender_mobile,
    receiver_mobile,
    fax_trans,
    SenderNativeCountry,
    receiverEmail,
    ip_address,
    agent_dollar_rate,
    ho_dollar_rate,
    bonus_amt,
    request_for_new_account,
    trans_mode,
    digital_id_sender,
    digital_id_payout,
    expected_payoutagentid,
    bonus_value_amount,
    bonus_type,
    bonus_on,
    ben_bank_id,
    ben_bank_name,
    test_Trn,
    paid_agent_id,
    send_sms,
    agent_settlement_rate,
    agent_ex_gain,
    cancel_date,
    cancel_by,
    agent_receiverCommission,
    agent_receiverSCommission,
    door_to_door,
    customer_sno,
    paid_date_usd_rate,
    send_sms_ben,
    extBankCommission,
    authorization_code,
    id_type,
    backup_approve_ts,
    backup_approve_by,
    authorization_req_by
FROM [{TABLE_SCHEMA}].[{TABLE_NAME}]
WHERE DOT >= '2009-07-08 00:00:00.000'
  AND DOT <  '2015-06-03 00:00:00.000';
"""

df = pd.read_sql(query, engine)

# Convert customer_sno from float to nullable integer

df["customer_sno"] = df["customer_sno"].astype("Int64")
df["Today_Dollar_rate"]=df["Today_Dollar_rate"].astype("Float64")

print(f"\nRows extracted: {len(df):,}")
print(f"Columns extracted: {len(df.columns)}")


# ============================================================
# 6. SQL SERVER DATA TYPE GROUPS
# ============================================================

STRING_TYPES = {
    "char", "varchar", "text",
    "nchar", "nvarchar", "ntext",
    "xml"
}

INTEGER_TYPES = {
    "bigint", "int", "smallint", "tinyint"
}

FLOAT_TYPES = {
    "float", "real"
}

BOOLEAN_TYPES = {
    "bit"
}

DATETIME_TYPES = {
    "date", "datetime", "datetime2",
    "smalldatetime", "datetimeoffset"
}

TIME_TYPES = {
    "time"
}

UUID_TYPES = {
    "uniqueidentifier"
}

BINARY_TYPES = {
    "binary", "varbinary", "image"
}

DECIMAL_TYPES = {
    "decimal", "numeric", "money", "smallmoney"
}


# ============================================================
# 7. CONVERT DATETIME COLUMNS TO MICROSECOND PRECISION
#
#    BigQuery works better with Parquet timestamp[us] than
#    timestamp[ns] for this workflow.
# ============================================================

for column, metadata in sql_metadata.items():

    if column not in df.columns:
        continue

    sql_type = metadata["DATA_TYPE"].lower()

    if sql_type in DATETIME_TYPES:

        df[column] = pd.to_datetime(
            df[column],
            errors="coerce"
        )

        # Convert pandas datetime64[ns] to datetime64[us].
        df[column] = df[column].astype("datetime64[us]")


# ============================================================
# 8. FIND COLUMNS THAT ARE 100% NULL
#
#    Example:
#        ReceiverFax: null
#        TestAnswer: null
#        SenderBankID: null
#
#    We use the original SQL Server metadata to give these
#    columns the correct Parquet type.
# ============================================================

all_null_columns = [
    column
    for column in df.columns
    if df[column].isna().all()
]

print("\nColumns containing only NULL:")

if all_null_columns:
    for column in all_null_columns:
        sql_type = sql_metadata[column]["DATA_TYPE"]
        print(f"  {column}: SQL Server type = {sql_type}")
else:
    print("  None")


# ============================================================
# 9. GIVE ALL-NULL PANDAS COLUMNS A USEFUL TYPE
#
#    This handles common SQL Server types.
# ============================================================

for column in all_null_columns:

    sql_type = sql_metadata[column]["DATA_TYPE"].lower()

    if sql_type in STRING_TYPES or sql_type in UUID_TYPES:
        df[column] = df[column].astype("string")

    elif sql_type == "bigint":
        df[column] = df[column].astype("Int64")

    elif sql_type == "int":
        df[column] = df[column].astype("Int64")

    elif sql_type == "smallint":
        df[column] = df[column].astype("Int64")

    elif sql_type == "tinyint":
        df[column] = df[column].astype("Int64")

    elif sql_type in FLOAT_TYPES:
        df[column] = df[column].astype("Float64")

    elif sql_type in BOOLEAN_TYPES:
        df[column] = df[column].astype("boolean")

    elif sql_type in DATETIME_TYPES:
        df[column] = pd.to_datetime(df[column]).astype("datetime64[us]")

    # decimal/numeric/money/time/binary columns are handled
    # explicitly in the Arrow table creation below.


# ============================================================
# 10. SHOW PANDAS DATA TYPES
# ============================================================

print("\nPandas data types:")
print(df.dtypes)


# ============================================================
# 11. CREATE PARQUET TABLE FROM PANDAS
#
#    For normal columns, PyArrow keeps the inferred type.
#    For all-NULL columns, we replace the NULL-only Arrow
#    column with an explicitly typed nullable Arrow array.
# ============================================================

arrow_table = pa.Table.from_pandas(
    df,
    preserve_index=False
)


def arrow_type_for_sql_type(metadata):
    """Return an Arrow type for an original SQL Server type."""

    sql_type = metadata["DATA_TYPE"].lower()

    if sql_type in STRING_TYPES or sql_type in UUID_TYPES:
        return pa.string()

    if sql_type == "bigint":
        return pa.int64()

    if sql_type == "int":
        return pa.int32()

    if sql_type == "smallint":
        return pa.int16()

    if sql_type == "tinyint":
        return pa.uint8()

    if sql_type in FLOAT_TYPES:
        return pa.float64()

    if sql_type in BOOLEAN_TYPES:
        return pa.bool_()

    if sql_type in DATETIME_TYPES:
        return pa.timestamp("us")

    if sql_type in TIME_TYPES:
        return pa.time64("us")

    if sql_type in BINARY_TYPES:
        return pa.binary()

    if sql_type == "money":
        return pa.decimal128(19, 4)

    if sql_type == "smallmoney":
        return pa.decimal128(10, 4)

    if sql_type in {"decimal", "numeric"}:
        precision = metadata["NUMERIC_PRECISION"] or 38
        scale = metadata["NUMERIC_SCALE"] or 0

        precision = min(int(precision), 38)
        scale = min(int(scale), precision)

        return pa.decimal128(precision, scale)

    # Safe fallback.
    return pa.string()


# Replace only columns whose extracted values are ALL NULL.
# This avoids changing the types of columns that contain real data.

for column in all_null_columns:

    metadata = sql_metadata[column]
    arrow_type = arrow_type_for_sql_type(metadata)

    null_array = pa.nulls(
        len(df),
        type=arrow_type
    )

    column_index = arrow_table.schema.get_field_index(column)

    arrow_table = arrow_table.set_column(
        column_index,
        column,
        null_array
    )


# ============================================================
# 12. WRITE PARQUET
# ============================================================

pq.write_table(
    arrow_table,
    OUTPUT_FILE,
    compression="snappy"
)

print(f"\nParquet file created: {OUTPUT_FILE}")

if os.path.exists(OUTPUT_FILE):
    file_size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"File size: {file_size_mb:.2f} MB")


# ============================================================
# 13. VERIFY PARQUET SCHEMA
# ============================================================

parquet_table = pq.read_table(OUTPUT_FILE)

print("\n================ PARQUET SCHEMA ================")
print(parquet_table.schema)


# ============================================================
# 14. VERIFY IMPORTANT DATETIME COLUMNS
# ============================================================

print("\n================ DATETIME COLUMNS ================")

datetime_check = [
    "DOT",
    "paidDate",
    "PODDate",
    "confirmDate",
    "lock_dot",
    "local_DOT",
    "cancel_date"
]

for column in datetime_check:

    if column in parquet_table.column_names:

        field = parquet_table.schema.field(column)

        print(f"{column}: {field.type}")


# ============================================================
# 15. VERIFY ALL-NULL COLUMNS
# ============================================================

print("\n================ ALL-NULL COLUMN TYPES ================")

for column in all_null_columns:

    field = parquet_table.schema.field(column)

    sql_type = sql_metadata[column]["DATA_TYPE"]

    print(
        f"{column}: "
        f"SQL Server={sql_type} -> "
        f"Parquet={field.type}"
    )


# ============================================================
# 16. READ PARQUET BACK WITH PANDAS
# ============================================================

parquet_df = pd.read_parquet(
    OUTPUT_FILE,
    engine="pyarrow"
)

print("\nParquet successfully read back into Pandas.")

if "DOT" in parquet_df.columns:
    print("\nFirst 5 DOT values:")
    print(parquet_df["DOT"].head())

print("\nPipeline completed successfully!")
