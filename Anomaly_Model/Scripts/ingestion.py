import requests
import pandas as pd
from io import BytesIO
import os
import boto3
import json
import sys
from dotenv import load_dotenv
from datetime import date

# Constants
BATCH_SIZE = 2100
S3_BUCKET = "financy"


# Gets all the tickers available in the EDGAR Database and other general company info
def get_company_data(user_agent):
    headers = {'User-Agent': user_agent}
    try:
        company_tickers = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers)
        company_tickers.raise_for_status()  # Ensure the request was successful
        company_data = pd.DataFrame.from_dict(company_tickers.json(), orient='index')
        # We need to add zeros because some CIKs differ in digits and the API needs 10 digit CIK.
        company_data['cik_str'] = company_data['cik_str'].astype(str).str.zfill(10)
        return company_data
    except requests.RequestException as e:
        print(f"Request exception: {e}")
        return pd.DataFrame()


# Selects a batch of company tickers based on the parameter inputted by the user
def select_company_data_batch(company_data, batch):
    start_index = (batch - 1) * BATCH_SIZE
    end_index = start_index + BATCH_SIZE
    if start_index >= len(company_data):
        raise ValueError("Batch number out of range (1-5)")
    return company_data[start_index:end_index]


# Fetches and returns 1 JSON company data based on the ticker inputted
def fetch_company_data_json(ticker, batch_company_data, user_agent):
    headers = {'User-Agent': user_agent}
    try:
        cik_val = str(batch_company_data.loc[batch_company_data['ticker'] == ticker, 'cik_str'].values[0])
        response = requests.get(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_val}.json', headers=headers)
        response.raise_for_status()  # Ensure the request was successful
        print(f"Successful CIK extraction for {ticker}")
        return response.json()
    except (requests.HTTPError, requests.RequestException) as e:
        print(f"Error for {ticker}: {e}")
        return None


# Upload every JSON file to the S3 bucket
def ticker_json_uploader(batch_company_data, user_agent, s3):
    tickers = list(batch_company_data['ticker'])
    counter_total_uploaded = 0
    counter_total_tries = 0
    today_date = str(date.today())

    for ticker in tickers:
        response_json = fetch_company_data_json(ticker, batch_company_data, user_agent)
        if response_json:
            
            try:
                # Convert JSON response to a string
                json_str = json.dumps(response_json)
                # 1st Encode the JSON string to json bytes
                json_bytes = json_str.encode("utf-8")
                print("Successfully converted to JSON bytes")

                # 2nd Compress the data using gzip, even if it's already in JSON format
                # compressed_data = BytesIO()
                # with gzip.GzipFile(fileobj=compressed_data, mode="wb") as gz:
                #    gz.write(file_content)
                # body = compressed_data.getvalue()

                # Preparing the JSON for S3 upload
                json_buffer = BytesIO()
                json_buffer.write(json_bytes)
                json_buffer.seek(0)
                # Defining the S3 bucket location
                s3_file_path = f"egdar_data/raw/{today_date}/{ticker}.json"
                # Upload to S3 bucket
                s3.upload_fileobj(json_buffer, S3_BUCKET, s3_file_path)
                print(f"Data for {ticker} uploaded to S3: {s3_file_path}")
                
                counter_total_uploaded += 1
                print("Total companies uploaded:", counter_total_uploaded)
            except Exception as e:
                print(f"Failed to upload {ticker} data: {e}")
            
        counter_total_tries += 1
        print("total tries:", counter_total_tries)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: script.py <user_agent> <batch_number>")
        sys.exit(1)

    user_agent = sys.argv[1]
    try:
        batch = int(sys.argv[2])
    except ValueError:
        print("Batch number must be an integer.")
        sys.exit(1)

    # Load variables from .env file
    load_dotenv()

    # AWS connection
    aws_access_key_id = os.getenv("aws_access_key_id")
    aws_secret_access_key = os.getenv("aws_secret_access_key")
    aws_session_token = os.getenv("aws_session_token")

    if not all([aws_access_key_id, aws_secret_access_key, aws_session_token]):
        print("Missing AWS credentials")
        sys.exit(1)

    s3 = boto3.client("s3",
                      aws_access_key_id=aws_access_key_id,
                      aws_secret_access_key=aws_secret_access_key,
                      aws_session_token=aws_session_token)

    # Get company data
    company_data = get_company_data(user_agent)
    if company_data.empty:
        print("Failed to fetch company data.")
        sys.exit(1)

    # Get batch of company data
    try:
        batch_company_data = select_company_data_batch(company_data, batch)
    except ValueError as e:
        print(e)
        sys.exit(1)

    # Upload JSON files to S3
    ticker_json_uploader(batch_company_data, user_agent, s3)
