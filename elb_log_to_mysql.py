import os
import gzip
import shlex
import boto3
import pandas as pd

from io import BytesIO
from urllib.parse import urlparse
from datetime import datetime
from pytz import timezone, utc
from sqlalchemy import create_engine
from dotenv import load_dotenv
from user_agents import parse as ua_parse

# Load .env config
load_dotenv()

# Set up database and S3 client
engine = create_engine(
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)
s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_DEFAULT_REGION')
)

# Extract log keys from S3 bucket
def extract_log_keys(bucket, prefix=''):
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    return [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.gz')]

def to_float(value):
    try:
        return float(value)
    except:
        return 0.0

# Parse each log line
def parse_log_line(line, source_file):
    try:
        parts = shlex.split(line)

        if len(parts) < 15:
            return None

        # Empty ELB name/malformed log
        if parts[2] == '-':
            return None

        # ELB or backend status code is missing or not a digit
        if not parts[8].isdigit() or not parts[9].isdigit():
            return None

         # Timestamp 
        timestamp = utc.localize(datetime.strptime(parts[1], '%Y-%m-%dT%H:%M:%S.%fZ')) \
            .astimezone(timezone('US/Eastern')) \
            .replace(microsecond=0, tzinfo=None)

        # Client IP
        client_ip = parts[3].split(':')[0]
        
        # ELB and Backend Status Codes
        elb_status_code = int(parts[8])
        backend_status_code = int(parts[9]) if parts[9].isdigit() else None

        # Bytes Received and Sent
        received_bytes = int(parts[10]) if parts[10].isdigit() else 0
        sent_bytes = int(parts[11]) if parts[11].isdigit() else 0

        # HTTP Method and Requested Path
        request_parts = parts[12].split()
        http_method = request_parts[0]
        full_url = request_parts[1]
        requested_path = urlparse(full_url).path

        # Total Processing Time
        total_processing_time_ms = sum(to_float(parts[i]) for i in [5, 6, 7]) * 1000

        # User Agent
        user_agent_full = parts[13]
        ua = ua_parse(user_agent_full)
        ua_os_family = ua.os.family or 'Other'
        ua_browser_family = ua.browser.family or 'Other'

       
        return {
            'log_timestamp': timestamp,
            'client_ip': client_ip,
            'http_method': http_method,
            'requested_path': requested_path,
            'elb_status_code': elb_status_code,
            'backend_status_code': backend_status_code,
            'total_processing_time_ms': total_processing_time_ms,
            'received_bytes': received_bytes,
            'sent_bytes': sent_bytes,
            'user_agent_full': user_agent_full,
            'ua_browser_family': ua_browser_family,
            'ua_os_family': ua_os_family,
            'log_source_file': source_file  
        }

    except:
        return None

# Transform logs into a dataframe
def transform_logs(bucket, keys):
    parsed_logs = []
    for key in keys:
        obj = s3.get_object(Bucket=bucket, Key=key)
        with gzip.GzipFile(fileobj=BytesIO(obj['Body'].read())) as gz:
            for line in gz:
                parsed = parse_log_line(line.decode('utf-8').strip(), key)
                if parsed:
                    parsed_logs.append(parsed)
    return pd.DataFrame(parsed_logs)

def load_to_mysql(df, table='elb_log_data'):
    if not df.empty:
        df.to_sql(table, con=engine, if_exists='append', index=False)
        print(f"✅ Inserted {len(df)} rows into `{table}`.")
    else:
        print("⚠️ No data to insert.")

def run_etl():
    bucket = os.getenv('S3_BUCKET')
    keys = extract_log_keys(bucket)
    df_parsed_logs = transform_logs(bucket, keys)
    load_to_mysql(df_parsed_logs)

if __name__ == "__main__":
    run_etl()
