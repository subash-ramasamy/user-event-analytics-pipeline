from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

PROJECT_DIR = "/Users/subashramasamy/Desktop/user-event-analytics-pipeline"
VENV = f"{PROJECT_DIR}/venv/bin/python"
DBT = f"{PROJECT_DIR}/venv/bin/dbt"
DBT_PROJECT = f"{PROJECT_DIR}/uea_dbt"

default_args = {
    "owner": "subash",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="uea_pipeline",
    default_args=default_args,
    description="User Event Analytics Pipeline",
    schedule="@daily",
    start_date=datetime(2026, 5, 22),
    catchup=False,
    tags=["uea", "fintech"],
) as dag:

    generate_users = BashOperator(
        task_id="generate_users",
        bash_command=f"{VENV} {PROJECT_DIR}/ingestion/generate_users.py",
    )

    generate_sessions = BashOperator(
        task_id="generate_sessions",
        bash_command=f"{VENV} {PROJECT_DIR}/ingestion/generate_sessions.py",
    )

    generate_events = BashOperator(
        task_id="generate_events",
        bash_command=f"{VENV} {PROJECT_DIR}/ingestion/generate_events.py",
    )

    validate_users = BashOperator(
        task_id="validate_users",
        bash_command=f"{VENV} {PROJECT_DIR}/expectations/validate_users.py",
    )

    validate_sessions = BashOperator(
        task_id="validate_sessions",
        bash_command=f"{VENV} {PROJECT_DIR}/expectations/validate_sessions.py",
    )

    validate_events = BashOperator(
        task_id="validate_events",
        bash_command=f"{VENV} {PROJECT_DIR}/expectations/validate_events.py",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_PROJECT} && {DBT} build --select staging marts",
    )

    generate_users >> validate_users >> generate_sessions >> validate_sessions >> generate_events >> validate_events >> dbt_run