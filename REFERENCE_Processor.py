import os
import logging
import boto3
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from io import StringIO
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# Access environment variables
DB_USERNAME = os.getenv('BDI_DB_USERNAME')
DB_PASSWORD = os.getenv('BDI_DB_PASSWORD')
DB_HOST = os.getenv('BDI_DB_HOST')
DB_PORT = os.getenv('BDI_DB_PORT', '5432')
DB_NAME = os.getenv('BDI_DB_NAME', 'postgres')
AWS_REGION = os.getenv('AWS_REGION')
S3_BUCKET = 'financy-ai'
S3_PREFIX = 'financy'

# AWS S3 client
s3_client = boto3.client('s3', region_name=AWS_REGION)

# Database credentials dictionary
db_credentials = {
    'dbname': DB_NAME,
    'user': DB_USERNAME,
    'password': DB_PASSWORD,
    'host': DB_HOST,
    'port': DB_PORT
}

def read_csv_from_s3(bucket, prefix):
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        files = [file['Key'] for file in response['Contents'] if file['Key'].endswith('.csv')]
        if not files:
            logging.info("No CSV files found in the bucket.")
            return None
        # Assuming you want to process the first CSV file found
        csv_file_key = files[0]
        csv_object = s3_client.get_object(Bucket=bucket, Key=csv_file_key)
        csv_data = csv_object['Body'].read().decode('utf-8')
        df = pd.read_csv(StringIO(csv_data), index_col=False)
        logging.info(f"CSV data from {csv_file_key} loaded into DataFrame.")
        return df
    except Exception as e:
        logging.error("Error reading CSV from S3: ", exc_info=True)
        return None

def csv_to_postgres(df: pd.DataFrame, ticker: str) -> str:
    try:
        logging.info("Connecting to the PostgreSQL database...")
        conn = psycopg2.connect(**db_credentials)
        cur = conn.cursor()
        logging.info("Successfully connected to the database.")

        # Create table name dynamically based on ticker
        table_name = f"{ticker.lower()}"
        logging.info(f"Preparing to create or confirm existence of table '{table_name}'.")

        # Define the SQL for table creation
        create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                "id" SERIAL PRIMARY KEY,
                "end" DATE,
                "val" BIGINT,
                "accn" VARCHAR(255),
                "fy" VARCHAR(10),
                "fp" VARCHAR(10),
                "form" VARCHAR(10),
                "filed" DATE,
                "frame" VARCHAR(255),
                "ticker" VARCHAR(10),
                "type" VARCHAR(255),
                "start" DATE
            );
        """
        cur.execute(create_table_query)
        logging.info(f"Table '{table_name}' created or already exists.")

        # Check if the "Unnamed: 0" column exists and drop it
        if "Unnamed: 0" in df.columns:
            df = df.drop("Unnamed: 0", axis=1)
            logging.info('Dropped the "Unnamed: 0" column.')
            
        
        # Default date for empty values
        default_date = pd.to_datetime('1900-01-01')

        # Fill empty values with default date using 'coerce' for parsing
        df['start'] = pd.to_datetime(df['start'], errors='coerce')
        df.fillna(default_date, inplace=True)
    
        # Replace missing values with None
        #df.fillna(value='bfill', inplace=True)
        #df['start'] = df['start'].fillna(value=np.nan)     
        #df['start'] = df['start'].replace('', np.nan) 
        #df['start'].fillna(value=None, inplace=True)

        #df['start'] = pd.to_datetime(df['start'], errors='coerce')  
        df['start'] = df['start'].apply(lambda x: x if pd.notnull(x) else None)  # Convert NaT to None
        columns = '", "'.join(df.columns)
        placeholders = ', '.join(['%s'] * len(df.columns))
        upsert_query = f"""
            INSERT INTO {table_name} ("{columns}") VALUES ({placeholders})
            ON CONFLICT (/* conflict key columns here */) DO NOTHING
        """
        
        conflict_keys = ['ticker', 'start']  # Replace with appropriate columns

        # Process data in chunks to avoid memory issues

        chunksize = 1000
        for i in range(0, len(df), chunksize):
            chunk_df = df.iloc[i:i + chunksize]

            #chunk_df.fillna(value=None, inplace=True)

            # Prepare upsert query with conflict keys
            upsert_query = f"""
                INSERT INTO {table_name} ("{columns}") VALUES ({placeholders})
                ON CONFLICT ({", ".join(conflict_keys)}) DO UPDATE SET
                /* Specify update actions for conflicting rows here */
            """

            # Execute upsert for each row, handling errors
            for index, row in chunk_df.iterrows():
                try:
                    cur.execute(upsert_query, tuple(row))
                    #cur.execute(upsert_query, tuple(row), conflict_keys=conflict_keys)
                    logging.info(f"Upserted row {index+i}")
                except Exception as e:
                    logging.error(f"Error upserting row {index+i}: {e}")

        # Commit changes and close connection
        conn.commit()
        cur.close()
        conn.close()
        logging.info("Database connection closed.")
        return "Data upserted successfully"
    except Exception as e:
        logging.error("An error occurred while upserting data: ", exc_info=True)
        return "An error occurred while upserting data"

if __name__ == "__main__":
    df = read_csv_from_s3(S3_BUCKET, S3_PREFIX)
    if df is not None:  # Check if data was actually retrieved
        ticker = 'LLY'  # Replace with your ticker
        result = csv_to_postgres(df, ticker)
        logging.info(result)
    else:
        logging.info("No CSV data found in S3 bucket.")
    