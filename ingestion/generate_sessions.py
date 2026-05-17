import uuid
import random
import pandas as pd
from faker import Faker
from google.cloud import bigquery
from datetime import timedelta, datetime

fake = Faker('en_IN')

DEVICES = ['Android', 'iOS', 'Web']
DEVICE_WEIGHTS = [7, 2, 1]

def get_user_ids():
    client = bigquery.Client(project = "user-event-analytics-pipeline")
    query = "SELECT user_id FROM `user-event-analytics-pipeline.uea_raw.users` WHERE user_id IS NOT NULL"
    df = client.query(query).to_dataframe()
    return df["user_id"].to_list()

generated_session_ids =[]

def generate_session(user_ids):
    if random.random() > 0.03 or len(generated_session_ids) == 0:
        session_id = str(uuid.uuid4())
    else:
        session_id = random.choice(generated_session_ids)
    
    generated_session_ids.append(session_id)
    
    start_time = fake.date_time_between(start_date='-1y', end_date='now')
    
    # 5% chance session_end is before session_start
    if random.random() > 0.05:
        end_time = start_time + timedelta(minutes=random.randint(5, 45))
    else:
        end_time = start_time - timedelta(minutes=random.randint(5, 45))
    
    return {
        "session_id": session_id,
        "user_id": random.choice(user_ids),
        "session_start": start_time,
        "session_end": end_time,
        "device": random.choices(DEVICES, weights=DEVICE_WEIGHTS)[0] if random.random() > 0.03 else None
    }

def generate_sessions(user_ids, n = 200):
    records = []
    for _ in range(n):
        records.append(generate_session(user_ids))
    return records

def load_to_bigquery(records):
    df = pd.DataFrame(records)
    client = bigquery.Client(project="user-event-analytics-pipeline")
    table_id = "user-event-analytics-pipeline.uea_raw.sessions"
    
    schema = [
        bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("session_start", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("session_end", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("device", "STRING", mode="NULLABLE"),
    ]
    
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    print(f"Loaded {len(df)} rows to {table_id}")

if __name__ == "__main__":
    user_ids = get_user_ids()
    records = generate_sessions(user_ids,200)
    load_to_bigquery(records)