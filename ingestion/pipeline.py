import logging
import sys
from generate_users import generate_users, load_to_bigquery as load_users
from generate_sessions import get_user_ids, generate_sessions, load_to_bigquery as load_sessions
from generate_events import get_sessions, generate_events, load_to_bigquery as load_events

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

def run_pipeline():
    try:
        logger.info("Starting pipeline...")

        logger.info("Step 1: Generating users...")
        users = generate_users(100)
        load_users(users)

        logger.info("Step 2: Generating sessions...")
        user_ids = get_user_ids()
        sessions = generate_sessions(user_ids, 200)
        load_sessions(sessions)

        logger.info("Step 3: Generating events...")
        sessions_data = get_sessions()
        events = generate_events(sessions_data, 700)
        load_events(events)

        logger.info("Pipeline completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_pipeline()