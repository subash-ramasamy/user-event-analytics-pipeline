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

def get_users_df():
    client = bigquery.Client(project=PROJECT_ID)
    query = f"SELECT * FROM `{PROJECT_ID}.uea_raw.users`"
    return client.query(query).to_dataframe()

def validate_users(df):
    context = gx.get_context()
    datasource = context.sources.add_pandas("users_source")
    asset = datasource.add_dataframe_asset("users_asset")
    batch_request = asset.build_batch_request(dataframe=df)
    
    context.add_or_update_expectation_suite("users_suite")
    validator = context.get_validator(
        batch_request=batch_request,
        expectation_suite_name="users_suite"
    )
     # user_id checks
    validator.expect_column_values_to_not_be_null("user_id", mostly=0.95)
    validator.expect_column_values_to_be_unique("user_id")
    
    # city checks
    validator.expect_column_values_to_be_in_set("city", ["Mumbai", "Delhi", "Bengaluru", "Chennai", "Hyderabad", "Pune", "Kolkata"], mostly=0.95)
    
    # device checks
    validator.expect_column_values_to_be_in_set("device", ["Android", "iOS", "Web"])
    
    # signup_date checks
    validator.expect_column_values_to_not_be_null("signup_date")
    
    # age_group checks
    validator.expect_column_values_to_be_in_set("age_group", ["18-25", "26-35", "36-50", "50+"], mostly=0.90)

    results = validator.validate()
    
    if not results["success"]:
        logger.error(f"Users validation failed: {results['statistics']}")
        raise ValueError("Users data quality check failed")
    
    logger.info(f"Users validation passed: {results['statistics']}")
    return results

if __name__ == "__main__":
    df = get_users_df()
    validate_users(df)