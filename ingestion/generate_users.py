import uuid
import random
import pandas as pd
from faker import Faker
from google.cloud import bigquery

fake = Faker('en_IN')

CITIES = ['Mumbai', 'Delhi', 'Bengaluru', 'Chennai', 'Hyderabad', 'Pune', 'Kolkata']
CITY_WEIGHTS = [3, 3, 4, 2, 2, 2, 1]

DEVICES = ['Android', 'iOS', 'Web']
DEVICE_WEIGHTS = [7, 2, 1]

AGE_GROUPS = ['18-25', '26-35', '36-50', '50+']
AGE_WEIGHTS = [4, 4, 2, 1]

def generate_user():
    return {
        "user_id":str(uuid.uuid4()) if random.random() > 0.02 else None,
        "city": random.choices(CITIES, weights = CITY_WEIGHTS)[0] if random.random() > 0.05 else None,
        "device": random.choices(DEVICES, weights=DEVICE_WEIGHTS)[0],
        "signup_date": fake.date_between(start_date='-2y', end_date='today'),
        "age_group": random.choices(AGE_GROUPS, weights=AGE_WEIGHTS)[0] if random.random() > 0.1 else None
    }

def generate_users(n=100):
    records = []
    for _ in range(n):
        records.append(generate_user())
    return records

def load_to_bigquery(records):
    df = pd.DataFrame(records)
    client = bigquery.Client(project="user-event-analytics-pipeline")
    table_id = "user-event-analytics-pipeline.uea_raw.users"
        
    schema = [
        bigquery.SchemaField("user_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("city", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("device", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("signup_date", "DATE", mode="NULLABLE"),
        bigquery.SchemaField("age_group", "STRING", mode="NULLABLE"),
    ]
    
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    print(f"Loaded {len(df)} rows to {table_id}")

if __name__ == "__main__":
    records = generate_users(100)
    load_to_bigquery(records)