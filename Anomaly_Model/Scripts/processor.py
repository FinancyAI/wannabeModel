import os
import logging
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

import pandas as pd
from dotenv import load_dotenv
from io import StringIO
import pandas as pd
import numpy as np
import json
import logging
import io
import csv
logger = logging.getLogger(__name__)

# Ajust based on your venv
import sys
#sys.path.append("/venv/lib/python3.11/site-packages")
import psycopg2


def process_json(list_of_tickers):
    list_of_keys = ["egdar_data/raw/2024-05-31/" + ticker + ".json" for ticker in list_of_tickers]
    all_records = []  # we get a list of dicts with all the features possible
    missing_files = []  # List to keep track of missing files
    processed_tickers = []
    
    # List the objects in the bucket
    """
    # couldn't be used because it has a limit of 1000 objects
    existing_keys = {obj['Key'] for obj in s3.list_objects_v2(Bucket=s3_bucket, Prefix="egdar_data/raw/2024-05-31/").get('Contents', [])}
    """
    existing_keys = []

    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=s3_bucket, Prefix="egdar_data/raw/2024-05-31/")

    for page in pages:
        for obj in page['Contents']:
            existing_keys.append(obj["Key"])

    for key in list_of_keys:
        # Split the string by '/' and take the last part
        file_name = key.split('/')[-1]
        # Split the last part by '.' and take the first part
        ticker = file_name.split('.')[0]

        if key not in existing_keys:
            missing_files.append(ticker)
            continue
        else:
            processed_tickers.append(ticker)
            

            # Download JSON file from S3
            response = s3.get_object(Bucket=s3_bucket, Key=key)
            compressed_data = response["Body"].read()  # not human readable data
                
            # Decompress the data - in our case the json werent compressed as gzip
            #with gzip.GzipFile(fileobj=BytesIO(compressed_data), mode="rb") as gz:
             #   decompressed_content = gz.read()  # string dictionary
                
            # Convert the decompressed content to a dictionary
            data = json.loads(compressed_data.decode("utf-8"))  # parsing json content to a dictionary
                    
            # Check if 'facts' key is present
            if 'facts' not in data:
                print(f"No 'facts' key for {ticker}")
                continue
    
            # Getting the set of units available
            reporting_types = list(data["facts"].keys())
    
            for reporting_type in reporting_types:  # iterating through reporting types
                # Getting the set of units available
                accounts = list(data["facts"][reporting_type].keys())
                
                list1 = []
                for account in accounts:
                    list1 += list(data["facts"][reporting_type][account]["units"].keys())
                
                units_list = list(set(list1))
    
                # Remember the data is organized by accounts. So for each account (type) we have a lot of records
                for acc_name, acc_values in data['facts'][reporting_type].items():  # iterating through accounts
                    for unit in units_list:  # iterating through units
                        r_data_list = acc_values.get('units', {}).get(unit, {})
                        for record in r_data_list:  # iterating through a list of dicts
                            record["reporting_type"] = reporting_type
                            record["units"] = unit
                            record["type"] = acc_name
                            record["ticker"] = ticker
                            all_records.append(record)

    # Select only relevant columns
    end_list = []
    for record in all_records:
        dict1 = {}
        dict1["end"] = record.get("end", {})
        dict1["ticker"] = record.get("ticker", {})
        dict1["reporting_type"] = record.get("reporting_type", {})
        dict1["form"] = record.get("form", {})
        dict1["type"] = record.get("type", {})
        dict1["units"] = record.get("units", {})
        dict1["val"] = record.get("val", {})
        end_list.append(dict1)
    
    print(f"\nTickers processed: {processed_tickers}")
    print("\nMissing files:", missing_files)
    return end_list


def delete_table_inRDS(db_name, db_username, db_password, db_host, db_port):

    try:
        conn = psycopg2.connect(dbname = db_name, user = db_username, password = db_password, host = db_host, port = db_port)
        cursor = conn.cursor()

        sql_query = """
            DROP TABLE edgar_selected_tickers_table;
                    """

        # Create a new db
        cursor.execute(sql_query)

        print("\nTable edgar_selected_tickers_table was deleted........\n")

        conn.commit()

        # Close the cursor and connection
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        print("Error:", e)


def create_table_inRDS(db_name, db_username, db_password, db_host, db_port):

    try:
        conn = psycopg2.connect(dbname = db_name, user = db_username, password = db_password, host = db_host, port = db_port)
        cursor = conn.cursor()

        sql_query = """
            CREATE TABLE IF NOT EXISTS edgar_selected_tickers_table (
            end_date DATE,
            ticker TEXT,
            reporting_type TEXT,
            form TEXT,
            type TEXT,
            units TEXT,
            val REAL
        );
                    """

        # Create a new db
        cursor.execute(sql_query)

        print("\nTable edgar_selected_tickers_table was/is created........\n")

        conn.commit()

        # Close the cursor and connection
        cursor.close()
        conn.close()

    except psycopg2.Error as e:
        print("Error:", e)


# Receives a list of dictionaries in bulk and loads them into aws postgres rds
def load_batch_into_database(batch_data, db_name, db_username, db_password, db_host, db_port):
    try:

        conn = psycopg2.connect(dbname = db_name, user = db_username, password = db_password, host = db_host, port = db_port)
        cursor = conn.cursor()

        # Convert list of dictionaries to CSV format
        csv_buffer = io.StringIO()
        csv_writer = csv.DictWriter(csv_buffer, fieldnames=batch_data[0].keys())
        csv_writer.writeheader()
        for record in batch_data:
            # Replace empty values with None
            record = {key: value if value != '' else None for key, value in record.items()}
            csv_writer.writerow(record)
        csv_buffer.seek(0)

        # Load CSV data into PostgreSQL database using cursor.copy_expert()
        copy_sql = "COPY edgar_selected_tickers_table FROM STDIN WITH CSV HEADER DELIMITER ',' NULL ''"
        cursor.copy_expert(copy_sql, csv_buffer)

        # Commit changes and close cursor and connection
        conn.commit()
        cursor.close()
        conn.close()

        print("\nbatch data was loaded with success! \n")

    except psycopg2.Error as e:
        print("Error:", e)




if __name__ == '__main__':

    load_dotenv() 

    aws_access_key_id = os.getenv("aws_access_key_id")
    aws_secret_access_key = os.getenv("aws_secret_access_key")
    aws_session_token = os.getenv("aws_session_token")
    s3_bucket = "financy"
    s3_prefix_path = "egdar_data/raw/"

    s3 = boto3.client("s3",
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key,
                        aws_session_token=aws_session_token)


    db_username = os.getenv('db_username')
    db_password = os.getenv("db_password")
    db_host = os.getenv("db_host")
    db_port = os.getenv("db_port")
    db_name = os.getenv("db_name")
    
    anomaly_tickers_list = pd.read_csv("../Data/Anomalies/Anomalies_tracker.csv")["Ticker"].unique().tolist()
    
    data_to_load = process_json(anomaly_tickers_list)
    delete_table_inRDS(db_name, db_username, db_password, db_host, db_port)
    create_table_inRDS(db_name, db_username, db_password, db_host, db_port)
    load_batch_into_database(data_to_load, db_name, db_username, db_password, db_host, db_port)
    
    
