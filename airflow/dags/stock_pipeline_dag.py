from datetime import datetime, timedelta
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator

# Make sure Airflow can import our script from /opt/airflow/scripts
sys.path.append("/opt/airflow/scripts")
from fetch_and_load import main as fetch_and_load_main

default_args = {
    "owner": "airflow",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="stock_data_pipeline",
    default_args=default_args,
    description="Fetch stock market data and load into Postgres",
    schedule_interval="@daily",  # you can change to hourly if needed
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["stocks"],
) as dag:

    fetch_and_load_task = PythonOperator(
        task_id="fetch_and_load_stock_data",
        python_callable=fetch_and_load_main,
    )

    fetch_and_load_task

