"""Airflow DAG: fetch CBR USD/EUR/CNY rates, process via PySpark, load into MongoDB.

Pipeline:
    fetch_cbr_rates (HTTP + validation)
        -> stage_raw_json (write batch for the Spark task)
        -> spark_process_and_load (KubernetesPodOperator running src/spark_job.py)

Retry policy: 3 retries, 5 minute delay, capped -- never infinite retry.
Idempotent: re-running for the same logical date upserts on (date, currency).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta

from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.utils.dates import days_ago

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.cbr_client import CbrClientError, fetch_cbr_rates  # noqa: E402
from src.logging_config import get_logger  # noqa: E402

logger = get_logger("cbr_rates_dag")

RAW_STAGING_DIR = os.environ.get("CBR_STAGING_DIR", "/opt/airflow/data/cbr_raw")
SPARK_IMAGE = os.environ.get("SPARK_JOB_IMAGE", "kubernetes-demo/spark-job:1.0.0")
NAMESPACE = os.environ.get("AIRFLOW_TASK_NAMESPACE", "data-platform")

default_args = {
    "owner": "data-platform",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
    "execution_timeout": timedelta(minutes=20),
}


def _staging_path(logical_date: datetime) -> str:
    return os.path.join(RAW_STAGING_DIR, f"cbr_rates_{logical_date.strftime('%Y-%m-%d')}.json")


def fetch_and_stage_cbr_rates(logical_date: datetime, **_context: object) -> str:
    """Fetch validated CBR rates and write them as newline-delimited JSON for Spark.

    Raises on any failure -- Airflow marks the task (and DAG run) failed
    rather than writing partial/corrupted data.
    """
    try:
        rates = fetch_cbr_rates(on_date=logical_date.date())
    except CbrClientError as exc:
        logger.error(
            "Failed to fetch CBR rates",
            extra={"extra_fields": {"error_type": type(exc).__name__, "detail": str(exc)}},
        )
        raise

    os.makedirs(RAW_STAGING_DIR, exist_ok=True)
    output_path = _staging_path(logical_date)
    with open(output_path, "w", encoding="utf-8") as fh:
        for point in rates:
            fh.write(
                json.dumps(
                    {
                        "date": point.rate_date.isoformat(),
                        "currency": point.currency,
                        "nominal": point.nominal,
                        "rate": point.rate,
                        "source": point.source,
                    }
                )
                + "\n"
            )

    logger.info(
        "Staged CBR rates",
        extra={"extra_fields": {"rows": len(rates), "path": output_path}},
    )
    return output_path


with DAG(
    dag_id="cbr_rates_pipeline",
    description="Download CBR USD/EUR/CNY rates, process with PySpark, load into MongoDB",
    default_args=default_args,
    schedule_interval="0 18 * * 1-5",  # 18:00 UTC on weekdays, after CBR publishes rates
    start_date=days_ago(1),
    catchup=False,
    max_active_runs=1,
    tags=["currency", "cbr", "mongodb", "pyspark"],
) as dag:
    fetch_task = PythonOperator(
        task_id="fetch_cbr_rates",
        python_callable=fetch_and_stage_cbr_rates,
        op_kwargs={"logical_date": "{{ logical_date }}"},
    )

    spark_task = KubernetesPodOperator(
        task_id="spark_process_and_load",
        name="cbr-spark-process-and-load",
        namespace=NAMESPACE,
        image=SPARK_IMAGE,
        cmds=["python3", "-m", "src.spark_job"],
        arguments=[
            "--input-path",
            "{{ ti.xcom_pull(task_ids='fetch_cbr_rates') }}",
        ],
        env_vars={
            "MONGODB_DATABASE": os.environ.get("MONGODB_DATABASE", "currency"),
            "MONGODB_COLLECTION": os.environ.get("MONGODB_COLLECTION", "rates"),
        },
        env_from=["mongodb-credentials"],
        service_account_name="airflow-spark-worker",
        get_logs=True,
        is_delete_operator_pod=True,
        startup_timeout_seconds=300,
    )

    fetch_task >> spark_task
