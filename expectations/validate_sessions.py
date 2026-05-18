import great_expectations as gx
import pandas as pd
from google.cloud import bigquery
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()
PROJECT_ID = os.getenv("GCP_PROJECT_ID")


def get_sessions_df():
    client = bigquery.Client(project=PROJECT_ID)
    query = f"SELECT * FROM `{PROJECT_ID}.uea_raw.sessions`"
    return client.query(query).to_dataframe()


def get_valid_user_ids():
    client = bigquery.Client(project=PROJECT_ID)
    query = f"SELECT DISTINCT user_id FROM `{PROJECT_ID}.uea_raw.users` WHERE user_id IS NOT NULL"
    df = client.query(query).to_dataframe()
    return df["user_id"].tolist()