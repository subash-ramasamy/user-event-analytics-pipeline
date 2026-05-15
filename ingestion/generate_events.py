import uuid
import random
import pandas as pd
from faker import Faker
from google.cloud import bigquery
from datetime import timedelta, datetime

fake = Faker('en_IN')

EVENT_TYPES = ['user_searched', 'restaurant_clicked', 'cart_added', 'order_placed', 'order_dropped']
EVENT_WEIGHTS = [35, 25, 20, 12, 8]

def get_sessions():
    client = bigquery.Client(project="user-event-analytics-pipeline")
    query = "SELECT session_id,user_id, session_start, session_end FROM `user-event-analytics-pipeline.uea_raw.sessions`"
    df = client.query(query).to_dataframe()
    return df.to_dict('records')

def generate_event(sessions):
    session = random.choice(sessions)
    session_start = session['session_start']
    session_end = session['session_end']
    
    event_timestamp = fake.date_time_between(
        start_date=session_start, 
        end_date=session_end
    )
    
    return {
        "event_id": str(uuid.uuid4()),
        "session_id": session['session_id'],
        "user_id": session['user_id'],
        "event_type": random.choices(EVENT_TYPES, weights=EVENT_WEIGHTS)[0],
        "event_timestamp": event_timestamp
    }

def generate_events(sessions, n=700):
    records = []
    for _ in range(n):
        records.append(generate_event(sessions))
    return records

def load_to_bigquery(records):
    df = pd.DataFrame(records)
    client = bigquery.Client(project="user-event-analytics-pipeline")
    table_id = "user-event-analytics-pipeline.uea_raw.events"
    
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
    
    client.load_table_from_dataframe(df, table_id, job_config=job_config)
    print(f"Loaded {len(df)} rows to {table_id}")

if __name__ == "__main__":
    sessions = get_sessions()
    records = generate_events(sessions, 700)
    load_to_bigquery(records)