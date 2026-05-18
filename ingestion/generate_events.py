import uuid
import random
import pandas as pd
import os
from dotenv import load_dotenv
from faker import Faker
from google.cloud import bigquery
from datetime import timedelta, datetime
import logging
logger = logging.getLogger(__name__)

load_dotenv()
PROJECT_ID = os.getenv("GCP_PROJECT_ID")

fake = Faker('en_IN')

EVENT_TYPES = ['user_searched', 'restaurant_clicked', 'cart_added', 'order_placed', 'order_dropped']
EVENT_WEIGHTS = [35, 25, 20, 12, 8]

def get_sessions():
    client = bigquery.Client(project=PROJECT_ID)
    query = f"SELECT session_id,user_id, session_start, session_end FROM `{PROJECT_ID}.uea_raw.sessions`"
    df = client.query(query).to_dataframe()
    return df.to_dict('records')

def generate_event(sessions):
    session = random.choice(sessions)
    session_start = session['session_start']
    session_end = session['session_end']
    
    # 2% chance timestamp is outside session window
    if random.random() > 0.02:
        event_timestamp = fake.date_time_between(start_date=session_start, end_date=session_end)
    else:
        event_timestamp = session_end + timedelta(minutes=random.randint(5, 60))
    
    return {
        "event_id": str(uuid.uuid4()),
        "session_id": session['session_id'],
        "user_id": session['user_id'],
        "event_type": random.choices(EVENT_TYPES, weights=EVENT_WEIGHTS)[0] if random.random() > 0.01 else 'payment_failed',
        "event_timestamp": event_timestamp
    }

def generate_events(sessions, n=700):
    records = []
    for _ in range(n):
        records.append(generate_event(sessions))
    return records

def load_to_bigquery(records):
    df = pd.DataFrame(records)
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.uea_raw.events"
    
    schema = [
        bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("event_type", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("event_timestamp", "TIMESTAMP", mode="NULLABLE"),
    ]
    
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND
    )
    try:
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        logger.info(f"Loaded {len(df)} rows to {table_id}")
        table = client.get_table(table_id)
        logger.info(f"Total rows in {table_id}: {table.num_rows:,}")
    except Exception as e:
        logger.error(f"failed to load to {table_id}: {e}")
        raise

if __name__ == "__main__":
    sessions = get_sessions()
    records = generate_events(sessions, 700)
    load_to_bigquery(records)