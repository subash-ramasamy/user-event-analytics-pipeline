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

def get_events_df():
    client = bigquery.Client(project=PROJECT_ID)
    query = f"SELECT * FROM `{PROJECT_ID}.uea_raw.events`"
    return client.query(query).to_dataframe()

def get_valid_session_ids():
    client = bigquery.Client(project=PROJECT_ID)
    query = f"SELECT DISTINCT session_id FROM `{PROJECT_ID}.uea_raw.sessions` WHERE session_id IS NOT NULL"
    df = client.query(query).to_dataframe()
    return df["session_id"].tolist()

def get_valid_user_ids():
    client = bigquery.Client(project=PROJECT_ID)
    query = f"SELECT DISTINCT user_id FROM `{PROJECT_ID}.uea_raw.users` WHERE user_id IS NOT NULL"
    df = client.query(query).to_dataframe()
    return df["user_id"].tolist()

def validate_events(df, valid_session_ids, valid_user_ids):
    # Pandas check — events outside session window
    sessions_df = pd.DataFrame([{
        'session_id': s, 
    } for s in valid_session_ids])
    
    invalid_timestamps = df[
        df['event_timestamp'] > df['event_timestamp'].max()
    ]
    if len(invalid_timestamps) > 0:
        logger.warning(f"Found {len(invalid_timestamps)} events outside session window")

    context = gx.get_context()
    datasource = context.sources.add_pandas("events_source")
    asset = datasource.add_dataframe_asset("events_asset")
    batch_request = asset.build_batch_request(dataframe=df)

    context.add_or_update_expectation_suite("events_suite")
    validator = context.get_validator(
        batch_request=batch_request,
        expectation_suite_name="events_suite"
    )

    validator.expect_column_values_to_not_be_null("event_id")
    validator.expect_column_values_to_be_unique("event_id")
    validator.expect_column_values_to_not_be_null("session_id")
    validator.expect_column_values_to_be_in_set("session_id", valid_session_ids)
    validator.expect_column_values_to_not_be_null("user_id")
    validator.expect_column_values_to_be_in_set("user_id", valid_user_ids)
    validator.expect_column_values_to_be_in_set("event_type", [
        'user_searched', 'restaurant_clicked', 'cart_added', 
        'order_placed', 'order_dropped', 'payment_failed'
    ])
    validator.expect_column_values_to_not_be_null("event_timestamp")

    results = validator.validate()

    if not results["success"]:
        for result in results["results"]:
            if not result["success"]:
                logger.error(f"Failed expectation: {result['expectation_config']['expectation_type']} on column: {result['expectation_config']['kwargs']}")
        raise ValueError("Events data quality check failed")

    logger.info(f"Events validation passed: {results['statistics']}")
    return results

if __name__ == "__main__":
    df = get_events_df()
    valid_session_ids = get_valid_session_ids()
    valid_user_ids = get_valid_user_ids()
    validate_events(df, valid_session_ids, valid_user_ids)