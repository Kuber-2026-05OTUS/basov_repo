"""PySpark job: validate, normalize, and load CBR currency rates into MongoDB.

Reads raw rate rows (as produced by `src.cbr_client`), enforces an explicit
schema, validates values, and writes to MongoDB via the MongoDB Spark
Connector. Designed to run as a KubernetesExecutor task from the Airflow DAG.

Pinned, compatible versions (see kubernetes-demo/airflow/README.md for the
full compatibility matrix):
  Python 3.11 | Java 17 (Temurin) | Spark 3.5.1 | MongoDB Spark Connector 10.3.0
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, IntegerType, StringType, StructField, StructType

from src.logging_config import get_logger

logger = get_logger("spark_job")

RAW_SCHEMA = StructType(
    [
        StructField("date", StringType(), nullable=False),
        StructField("currency", StringType(), nullable=False),
        StructField("nominal", IntegerType(), nullable=False),
        StructField("rate", DoubleType(), nullable=False),
        StructField("source", StringType(), nullable=False),
    ]
)

REQUIRED_CURRENCIES = ("USD", "EUR", "CNY")


class SparkJobValidationError(Exception):
    """Raised when the input batch fails schema/business validation."""


def build_spark_session(app_name: str, mongo_uri: str) -> SparkSession:
    """Create a SparkSession wired to the MongoDB Spark Connector."""
    return (
        SparkSession.builder.appName(app_name)
        .config("spark.mongodb.write.connection.uri", mongo_uri)
        .config(
            "spark.jars.packages",
            "org.mongodb.spark:mongo-spark-connector_2.12:10.3.0",
        )
        .getOrCreate()
    )


def validate_and_normalize(df: DataFrame) -> DataFrame:
    """Validate rows against the explicit schema and business rules.

    Rejects (raises) if: required currencies are missing, dates are
    malformed, nominal/rate are non-positive, or duplicate (date, currency)
    keys exist within the same batch.
    """
    total = df.count()
    if total == 0:
        raise SparkJobValidationError("Input batch is empty")

    null_counts = df.select(
        [F.count(F.when(F.col(c).isNull(), c)).alias(c) for c in RAW_SCHEMA.fieldNames()]
    ).first()
    if null_counts is not None:
        missing_fields = [c for c in RAW_SCHEMA.fieldNames() if null_counts[c] > 0]
        if missing_fields:
            raise SparkJobValidationError(f"Null values found in required fields: {missing_fields}")

    invalid = df.filter((F.col("nominal") <= 0) | (F.col("rate") <= 0)).count()
    if invalid > 0:
        raise SparkJobValidationError(f"{invalid} row(s) have non-positive nominal/rate")

    normalized = df.withColumn("date", F.to_date("date", "yyyy-MM-dd"))
    bad_dates = normalized.filter(F.col("date").isNull()).count()
    if bad_dates > 0:
        raise SparkJobValidationError(f"{bad_dates} row(s) have unparseable dates")

    dup_count = (
        normalized.groupBy("date", "currency").count().filter(F.col("count") > 1).count()
    )
    if dup_count > 0:
        raise SparkJobValidationError("Duplicate (date, currency) rows found in batch")

    distinct_currency_rows = normalized.select("currency").distinct().collect()
    present_currencies = {row["currency"] for row in distinct_currency_rows}
    missing_currencies = set(REQUIRED_CURRENCIES) - present_currencies
    if missing_currencies:
        raise SparkJobValidationError(f"Missing required currencies: {sorted(missing_currencies)}")

    return normalized.withColumn(
        "date", F.date_format("date", "yyyy-MM-dd")
    ).withColumn("loaded_at", F.lit(datetime.now(UTC).isoformat()))


def write_to_mongo(df: DataFrame, database: str, collection: str) -> None:
    """Write the normalized DataFrame to MongoDB via the Spark Connector."""
    (
        df.write.format("mongodb")
        .mode("append")
        .option("database", database)
        .option("collection", collection)
        .save()
    )


def run(input_path: str, mongo_uri: str, database: str, collection: str) -> None:
    """Entry point: read raw JSON rows, validate/normalize, write to MongoDB."""
    spark = build_spark_session("cbr-rates-processing", mongo_uri)
    try:
        raw_df = spark.read.schema(RAW_SCHEMA).json(input_path)
        normalized_df = validate_and_normalize(raw_df)
        write_to_mongo(normalized_df, database, collection)
        logger.info(
            "Spark job completed", extra={"extra_fields": {"rows": normalized_df.count()}}
        )
    finally:
        spark.stop()


def main() -> int:
    parser = argparse.ArgumentParser(description="CBR rates PySpark processing job")
    parser.add_argument("--input-path", required=True, help="Path to newline-delimited JSON input")
    parser.add_argument(
        "--database", default=os.environ.get("MONGODB_DATABASE", "currency")
    )
    parser.add_argument(
        "--collection", default=os.environ.get("MONGODB_COLLECTION", "rates")
    )
    args = parser.parse_args()

    mongo_uri = os.environ.get("MONGODB_URI")
    if not mongo_uri:
        logger.error(
            "MONGODB_URI is not set",
            extra={"extra_fields": {"error_type": "ConfigError"}},
        )
        return 1

    try:
        run(args.input_path, mongo_uri, args.database, args.collection)
    except SparkJobValidationError as exc:
        logger.error(
            "Validation failed",
            extra={
                "extra_fields": {
                    "error_type": "SparkJobValidationError",
                    "detail": str(exc),
                }
            },
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
