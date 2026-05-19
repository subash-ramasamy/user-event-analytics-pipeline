import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from generate_users import generate_users, load_to_bigquery as load_users, get_existing_user_ids
from generate_sessions import get_user_ids, generate_sessions, load_to_bigquery as load_sessions
from generate_events import get_sessions, generate_events, load_to_bigquery as load_events
from expectations.validate_users import validate_users, get_users_df
from expectations.validate_sessions import validate_sessions, get_sessions_df, get_valid_user_ids
from expectations.validate_events import validate_events, get_events_df, get_valid_session_ids

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

def run_pipeline():
    try:
        logger.info("Starting pipeline...")

        # Step 1: Load all raw data
        logger.info("Step 1: Generating and loading users...")
        new_users = generate_users(20)
        load_users(new_users)

        logger.info("Step 2: Generating and loading sessions...")
        all_user_ids = get_existing_user_ids()
        sessions = generate_sessions(all_user_ids, 200)
        load_sessions(sessions)

        logger.info("Step 3: Generating and loading events...")
        sessions_data = get_sessions()
        events = generate_events(sessions_data, 700)
        load_events(events)

        # Step 2: Validate raw data
        logger.info("Step 4: Validating users...")
        users_df = get_users_df()
        validate_users(users_df)

        logger.info("Step 5: Validating sessions...")
        sessions_df = get_sessions_df()
        valid_user_ids = get_valid_user_ids()
        validate_sessions(sessions_df, valid_user_ids)

        logger.info("Step 6: Validating events...")
        events_df = get_events_df()
        valid_session_ids = get_valid_session_ids()
        validate_events(events_df, valid_session_ids, valid_user_ids)

        logger.info("All validations passed. Ready for dbt.")
        logger.info("Pipeline completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_pipeline()