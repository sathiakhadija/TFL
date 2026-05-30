import os
from datetime import datetime

import psycopg2
from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from ingestion.station_disruptions import (
    ingest_station_disruptions,
    validate_station_disruptions,
)
from ingestion.tfl_client import TfLClient

default_args = {
    "owner": "tfl-pipeline",
    "retries": 2,
    "retry_delay": 30,
}


def _check_api_health(**context):
    client = TfLClient(
        api_key=os.environ["TFL_API_KEY"],
        app_id=os.environ.get("TFL_APP_ID"),
    )
    if not client.health_check():
        raise AirflowException("TfL API unreachable — aborting ingestion run")


def _ingest_station_disruptions(**context):
    conn = psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
    try:
        client = TfLClient(
            api_key=os.environ["TFL_API_KEY"],
            app_id=os.environ.get("TFL_APP_ID"),
        )
        row_count = ingest_station_disruptions(conn, client)
        context["ti"].xcom_push(key="row_count", value=row_count)
    finally:
        conn.close()


def _validate_ingestion(**context):
    conn = psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
    try:
        result = validate_station_disruptions(conn)
        if not result["valid"]:
            raise AirflowException(
                f"station_disruptions validation failed: {result['checks']} "
                f"(row_count={result['row_count']})"
            )
    finally:
        conn.close()


with DAG(
    dag_id="station_disruptions_ingestion",
    schedule="*/30 * * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["tfl", "ingestion", "station-disruptions"],
) as dag:

    check_api_health = PythonOperator(
        task_id="check_api_health",
        python_callable=_check_api_health,
    )

    ingest = PythonOperator(
        task_id="ingest_station_disruptions",
        python_callable=_ingest_station_disruptions,
    )

    validate_ingestion = PythonOperator(
        task_id="validate_ingestion",
        python_callable=_validate_ingestion,
    )

    trigger_dbt = BashOperator(
        task_id="trigger_dbt",
        bash_command=(
            "dbt run "
            "--select staging.stg_station_disruptions "
            "marts.mart_station_reliability marts.mart_disruption_trends "
            "--profiles-dir $DBT_PROFILES_DIR "
            "--project-dir $DBT_PROFILES_DIR "
            "&& dbt test "
            "--select staging.stg_station_disruptions "
            "--profiles-dir $DBT_PROFILES_DIR "
            "--project-dir $DBT_PROFILES_DIR"
        ),
    )

    check_api_health >> ingest >> validate_ingestion >> trigger_dbt
