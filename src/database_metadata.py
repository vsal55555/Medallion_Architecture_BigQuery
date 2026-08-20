import json
from datetime import date, datetime
from decimal import Decimal

import pyodbc
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# Configuration
SERVER = r"DESKTOP-75UOVBF"
DATABASE = "Kist_Msia_DB"
DRIVER = "ODBC Driver 17 for SQL Server"

TABLE_SCHEMA = "dbo"
TABLE_NAME = "moneysend"
OUTPUT_FILE = "moneysend.schema.json"


def rows_to_dicts(result):
    return [dict(row) for row in result.mappings().all()]


def clean_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bytes):
        return value.hex()
    return value


def clean_rows(rows):
    return [
        {key: clean_value(value) for key, value in row.items()}
        for row in rows
    ]


# Check ODBC driver
available_drivers = pyodbc.drivers()
print("Available ODBC drivers:", available_drivers)

if DRIVER not in available_drivers:
    raise RuntimeError(
        f"{DRIVER!r} was not found. Available drivers: {available_drivers}"
    )

# SQL Server connection using Windows Authentication
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

# Verify connection
with engine.connect() as connection:
    print("SQL Server connection successful!")


params = {
    "schema_name": TABLE_SCHEMA,
    "table_name": TABLE_NAME,
}

# 1. INFORMATION_SCHEMA.COLUMNS
columns_query = text("""
SELECT
    TABLE_CATALOG,
    TABLE_SCHEMA,
    TABLE_NAME,
    COLUMN_NAME,
    ORDINAL_POSITION,
    COLUMN_DEFAULT,
    IS_NULLABLE,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    CHARACTER_OCTET_LENGTH,
    NUMERIC_PRECISION,
    NUMERIC_PRECISION_RADIX,
    NUMERIC_SCALE,
    DATETIME_PRECISION,
    COLLATION_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = :schema_name
  AND TABLE_NAME = :table_name
ORDER BY ORDINAL_POSITION;
""")

# 2. sys.tables
tables_query = text("""
SELECT
    t.object_id,
    t.name AS table_name,
    SCHEMA_NAME(t.schema_id) AS schema_name,
    t.create_date,
    t.modify_date,
    t.is_ms_shipped,
    t.temporal_type,
    t.temporal_type_desc,
    t.is_memory_optimized,
    t.durability_desc
FROM sys.tables AS t
WHERE t.schema_id = SCHEMA_ID(:schema_name)
  AND t.name = :table_name;
""")

# 3. sys.columns
sys_columns_query = text("""
SELECT
    c.object_id,
    c.column_id,
    c.name AS column_name,

    SCHEMA_NAME(ty.schema_id) AS type_schema_name,
    ty.name AS user_type_name,
    st.name AS system_type_name,

    c.max_length,
    c.precision,
    c.scale,
    c.collation_name,

    c.is_nullable,
    c.is_ansi_padded,
    c.is_rowguidcol,
    c.is_identity,
    c.is_computed,
    c.is_filestream,

    c.generated_always_type,
    c.generated_always_type_desc

FROM sys.columns AS c

INNER JOIN sys.tables AS t
    ON t.object_id = c.object_id

INNER JOIN sys.types AS ty
    ON c.user_type_id = ty.user_type_id
   AND c.system_type_id = ty.system_type_id

INNER JOIN sys.types AS st
    ON c.system_type_id = st.user_type_id
   AND st.user_type_id = st.system_type_id

WHERE t.schema_id = SCHEMA_ID(:schema_name)
  AND t.name = :table_name

ORDER BY c.column_id;
""")

# 4. sys.indexes
indexes_query = text("""
SELECT
    i.object_id,
    i.index_id,
    i.name AS index_name,
    i.type AS index_type,
    i.type_desc AS index_type_desc,
    i.is_unique,
    i.is_primary_key,
    i.is_unique_constraint,
    i.is_disabled,
    i.is_hypothetical,
    i.has_filter,
    i.filter_definition
FROM sys.indexes AS i
INNER JOIN sys.tables AS t
    ON t.object_id = i.object_id
WHERE t.schema_id = SCHEMA_ID(:schema_name)
  AND t.name = :table_name
  AND i.index_id > 0
ORDER BY i.index_id;
""")

# 5. sys.index_columns
index_columns_query = text("""
SELECT
    ic.object_id,
    ic.index_id,
    ic.index_column_id,
    ic.key_ordinal,
    ic.partition_ordinal,
    ic.is_descending_key,
    ic.is_included_column,
    ic.column_id,
    c.name AS column_name
FROM sys.index_columns AS ic
INNER JOIN sys.tables AS t
    ON t.object_id = ic.object_id
INNER JOIN sys.columns AS c
    ON c.object_id = ic.object_id
   AND c.column_id = ic.column_id
WHERE t.schema_id = SCHEMA_ID(:schema_name)
  AND t.name = :table_name
ORDER BY ic.index_id, ic.key_ordinal, ic.index_column_id;
""")

# 6. sys.foreign_keys
foreign_keys_query = text("""
SELECT
    fk.object_id AS foreign_key_object_id,
    fk.name AS foreign_key_name,
    fk.parent_object_id,
    OBJECT_SCHEMA_NAME(fk.parent_object_id) AS parent_schema_name,
    OBJECT_NAME(fk.parent_object_id) AS parent_table_name,
    fk.referenced_object_id,
    OBJECT_SCHEMA_NAME(fk.referenced_object_id) AS referenced_schema_name,
    OBJECT_NAME(fk.referenced_object_id) AS referenced_table_name,
    fk.key_index_id,
    fk.is_disabled,
    fk.is_not_for_replication,
    fk.is_not_trusted,
    fk.delete_referential_action,
    fk.delete_referential_action_desc,
    fk.update_referential_action,
    fk.update_referential_action_desc
FROM sys.foreign_keys AS fk
WHERE fk.parent_object_id = OBJECT_ID(
    QUOTENAME(:schema_name) + '.' + QUOTENAME(:table_name)
)
   OR fk.referenced_object_id = OBJECT_ID(
    QUOTENAME(:schema_name) + '.' + QUOTENAME(:table_name)
)
ORDER BY fk.name;
""")

# 7. sys.foreign_key_columns
foreign_key_columns_query = text("""
SELECT
    fkc.constraint_object_id AS foreign_key_object_id,
    OBJECT_NAME(fkc.constraint_object_id) AS foreign_key_name,
    fkc.constraint_column_id,
    fkc.parent_object_id,
    OBJECT_SCHEMA_NAME(fkc.parent_object_id) AS parent_schema_name,
    OBJECT_NAME(fkc.parent_object_id) AS parent_table_name,
    fkc.parent_column_id,
    pc.name AS parent_column_name,
    fkc.referenced_object_id,
    OBJECT_SCHEMA_NAME(fkc.referenced_object_id) AS referenced_schema_name,
    OBJECT_NAME(fkc.referenced_object_id) AS referenced_table_name,
    fkc.referenced_column_id,
    rc.name AS referenced_column_name
FROM sys.foreign_key_columns AS fkc
INNER JOIN sys.columns AS pc
    ON pc.object_id = fkc.parent_object_id
   AND pc.column_id = fkc.parent_column_id
INNER JOIN sys.columns AS rc
    ON rc.object_id = fkc.referenced_object_id
   AND rc.column_id = fkc.referenced_column_id
WHERE fkc.parent_object_id = OBJECT_ID(
    QUOTENAME(:schema_name) + '.' + QUOTENAME(:table_name)
)
   OR fkc.referenced_object_id = OBJECT_ID(
    QUOTENAME(:schema_name) + '.' + QUOTENAME(:table_name)
)
ORDER BY fkc.constraint_object_id, fkc.constraint_column_id;
""")

# 8. sys.default_constraints
default_constraints_query = text("""
SELECT
    dc.object_id AS default_constraint_object_id,
    dc.name AS default_constraint_name,
    dc.parent_object_id,
    OBJECT_SCHEMA_NAME(dc.parent_object_id) AS schema_name,
    OBJECT_NAME(dc.parent_object_id) AS table_name,
    dc.parent_column_id,
    c.name AS column_name,
    dc.definition,
    dc.is_system_named
FROM sys.default_constraints AS dc
INNER JOIN sys.columns AS c
    ON c.object_id = dc.parent_object_id
   AND c.column_id = dc.parent_column_id
WHERE dc.parent_object_id = OBJECT_ID(
    QUOTENAME(:schema_name) + '.' + QUOTENAME(:table_name)
)
ORDER BY c.column_id;
""")

# 9. sys.check_constraints
check_constraints_query = text("""
SELECT
    cc.object_id AS check_constraint_object_id,
    cc.name AS check_constraint_name,
    cc.parent_object_id,
    OBJECT_SCHEMA_NAME(cc.parent_object_id) AS schema_name,
    OBJECT_NAME(cc.parent_object_id) AS table_name,
    cc.parent_column_id,
    CASE
        WHEN cc.parent_column_id = 0 THEN NULL
        ELSE c.name
    END AS column_name,
    cc.definition,
    cc.is_disabled,
    cc.is_not_for_replication,
    cc.is_not_trusted,
    cc.is_system_named
FROM sys.check_constraints AS cc
LEFT JOIN sys.columns AS c
    ON c.object_id = cc.parent_object_id
   AND c.column_id = cc.parent_column_id
WHERE cc.parent_object_id = OBJECT_ID(
    QUOTENAME(:schema_name) + '.' + QUOTENAME(:table_name)
)
ORDER BY cc.name;
""")


# Execute metadata queries
with engine.connect() as connection:
    columns = rows_to_dicts(connection.execute(columns_query, params))
    table = rows_to_dicts(connection.execute(tables_query, params))
    sys_columns = rows_to_dicts(connection.execute(sys_columns_query, params))
    indexes = rows_to_dicts(connection.execute(indexes_query, params))
    index_columns = rows_to_dicts(connection.execute(index_columns_query, params))
    foreign_keys = rows_to_dicts(connection.execute(foreign_keys_query, params))
    foreign_key_columns = rows_to_dicts(
        connection.execute(foreign_key_columns_query, params)
    )
    default_constraints = rows_to_dicts(
        connection.execute(default_constraints_query, params)
    )
    check_constraints = rows_to_dicts(
        connection.execute(check_constraints_query, params)
    )


# Build primary-key metadata, including composite keys
primary_keys = []

for index in indexes:
    if not index["is_primary_key"]:
        continue

    key_columns = [
        row for row in index_columns
        if row["index_id"] == index["index_id"]
        and row["key_ordinal"] > 0
    ]
    key_columns.sort(key=lambda x: x["key_ordinal"])

    primary_keys.append({
        "constraint_name": index["index_name"],
        "columns": [row["column_name"] for row in key_columns],
        "is_unique": bool(index["is_unique"]),
    })


# Build unique-index metadata
unique_indexes = []

for index in indexes:
    if not index["is_unique"] or index["is_primary_key"]:
        continue

    key_columns = [
        row for row in index_columns
        if row["index_id"] == index["index_id"]
        and row["key_ordinal"] > 0
    ]
    key_columns.sort(key=lambda x: x["key_ordinal"])

    unique_indexes.append({
        "name": index["index_name"],
        "columns": [row["column_name"] for row in key_columns],
        "is_unique_constraint": bool(index["is_unique_constraint"]),
        "is_disabled": bool(index["is_disabled"]),
    })


# Build foreign-key relationships, including composite FKs
foreign_key_map = {}

for fk in foreign_keys:
    fk_id = fk["foreign_key_object_id"]

    foreign_key_map[fk_id] = {
        "name": fk["foreign_key_name"],
        "parent_schema": fk["parent_schema_name"],
        "parent_table": fk["parent_table_name"],
        "referenced_schema": fk["referenced_schema_name"],
        "referenced_table": fk["referenced_table_name"],
        "columns": [],
        "delete_action": fk["delete_referential_action_desc"],
        "update_action": fk["update_referential_action_desc"],
        "is_disabled": bool(fk["is_disabled"]),
        "is_not_trusted": bool(fk["is_not_trusted"]),
    }

for row in foreign_key_columns:
    fk_id = row["foreign_key_object_id"]

    if fk_id in foreign_key_map:
        foreign_key_map[fk_id]["columns"].append({
            "ordinal": row["constraint_column_id"],
            "parent_column": row["parent_column_name"],
            "referenced_column": row["referenced_column_name"],
        })

foreign_keys_output = list(foreign_key_map.values())

for fk in foreign_keys_output:
    fk["columns"].sort(key=lambda x: x["ordinal"])


# Final JSON document
metadata = {
    "metadata_version": "1.0",

    "source": {
        "database_engine": "Microsoft SQL Server",
        "server": SERVER,
        "database": DATABASE,
        "schema": TABLE_SCHEMA,
        "table": TABLE_NAME,
    },

    "table": {
        "sys_tables": clean_rows(table),
    },

    "columns": {
        "information_schema": clean_rows(columns),
        "sys_columns": clean_rows(sys_columns),
    },

    "indexes": {
        "sys_indexes": clean_rows(indexes),
        "sys_index_columns": clean_rows(index_columns),
        "primary_keys": primary_keys,
        "unique_indexes": unique_indexes,
    },

    "foreign_keys": {
        "sys_foreign_keys": clean_rows(foreign_keys),
        "sys_foreign_key_columns": clean_rows(foreign_key_columns),
        "relationships": foreign_keys_output,
    },

    "default_constraints": clean_rows(default_constraints),

    "check_constraints": clean_rows(check_constraints),
}


# Write JSON
with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
    json.dump(
        metadata,
        file,
        indent=2,
        ensure_ascii=False,
    )


# Summary
print("\n==============================================")
print("DATABASE METADATA EXTRACTION COMPLETED")
print("==============================================")
print(f"Database : {DATABASE}")
print(f"Table    : {TABLE_SCHEMA}.{TABLE_NAME}")
print(f"Columns              : {len(columns)}")
print(f"Indexes              : {len(indexes)}")
print(f"Primary keys         : {len(primary_keys)}")
print(f"Unique indexes       : {len(unique_indexes)}")
print(f"Foreign keys         : {len(foreign_keys_output)}")
print(f"Default constraints  : {len(default_constraints)}")
print(f"Check constraints    : {len(check_constraints)}")
print(f"\nMetadata file created: {OUTPUT_FILE}")
