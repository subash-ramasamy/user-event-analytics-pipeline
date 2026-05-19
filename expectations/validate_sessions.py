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

def validate_sessions(df, valid_user_ids):
    # Pandas check — GE can't compare two columns
    invalid = df[df['session_end'] < df['session_start']]
    if len(invalid) > 0:
        logger.warning(f"Found {len(invalid)} sessions where session_end is before session_start")

    context = gx.get_context()
    datasource = context.sources.add_pandas("sessions_source")
    asset = datasource.add_dataframe_asset("sessions_asset")
    batch_request = asset.build_batch_request(dataframe=df)

    context.add_or_update_expectation_suite("sessions_suite")
    validator = context.get_validator(
        batch_request=batch_request,
        expectation_suite_name="sessions_suite"
    )

    validator.expect_column_values_to_not_be_null("session_id")
    validator.expect_column_values_to_be_unique("session_id")
    validator.expect_column_values_to_not_be_null("user_id")
    validator.expect_column_values_to_be_in_set("user_id", valid_user_ids)
    validator.expect_column_values_to_be_in_set("device", ["Android", "iOS", "Web"], mostly=0.97)
    validator.expect_column_values_to_not_be_null("session_start")
    validator.expect_column_values_to_not_be_null("session_end")

    results = validator.validate()

    if not results["success"]:
        for result in results["results"]:
            if not result["success"]:
                logger.error(f"Failed expectation: {result['expectation_config']['expectation_type']} on column: {result['expectation_config']['kwargs']}")
        raise ValueError("Sessions data quality check failed")

    logger.info(f"Sessions validation passed: {results['statistics']}")
    return results


if __name__ == "__main__":
    df = get_sessions_df()
    valid_user_ids = get_valid_user_ids()
    validate_sessions(df, valid_user_ids)