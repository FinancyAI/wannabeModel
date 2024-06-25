from dotenv import load_dotenv
import os
import boto3
import json
import pandas as pd
import pickle
import warnings
warnings.filterwarnings("ignore")

# Loading Feature Engineering tools
with open('Anomaly_Model/Model/imputer.pkl', 'rb') as file:
    imputer = pickle.load(file)
with open('Anomaly_Model/Model/scaler.pkl', 'rb') as file:
    scaler = pickle.load(file)

# Loading Model
with open('Anomaly_Model/Model/best_model.pkl', 'rb') as file:
    model = pickle.load(file)


columns_to_filter = ['end_date',
 'year',
 'ticker',
 'form',
 'Assets',
 'EarningsPerShareBasic',
 'EarningsPerShareDiluted',
 'LiabilitiesAndStockholdersEquity',
 'NetIncomeLoss',
 'RetainedEarningsAccumulatedDeficit',
 'StockholdersEquity']


def existent_tickers():
    existing_keys = []

    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=s3_bucket, Prefix="egdar_data/raw/")

    for page in pages:
        for obj in page['Contents']:
            existing_keys.append(obj["Key"])

    existent_tickers = []
    for key in existing_keys:
        file_name = key.split('/')[-1]
        # Split the last part by '.' and take the first part
        ticker = file_name.split('.')[0]
        existent_tickers.append(ticker)
    return existent_tickers


def is_ticker_available(ticker, existent_tickers):
    if ticker in existent_tickers:
        print("Ticker found in our records !")
        return True
    else:
        print("Ticker not found in our records :(")
        return False


def pull_data_for_ticker(ticker):
    key = "egdar_data/raw/2024-05-31/" + ticker + ".json"

    all_records = []  # we get a list of dicts with all the features possible

    # Download JSON file from S3
    response = s3.get_object(Bucket=s3_bucket, Key=key)
    compressed_data = response["Body"].read()  # not human readable data

    # Convert the decompressed content to a dictionary
    data = json.loads(compressed_data.decode("utf-8"))  # parsing json content to a dictionary

    # Check if 'facts' key is present
    if 'facts' not in data:
        print(f"No 'facts' key for {ticker}")
        return None  # Return None

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


    df = pd.DataFrame(end_list)
    return df


def preprocessing_df(df):

    # Change data types
    df["end"] = pd.to_datetime(df["end"])
    df.rename(columns={"end": "end_date"}, inplace=True)
    df["year"] = df["end_date"].apply(lambda x: int(x.strftime("%Y")))
    # Reordering columns
    df = df.iloc[:, [0, 7, 1, 2, 3, 4, 5, 6]]
    # Filtering for us-gaap reports
    df = df[df["reporting_type"] == "us-gaap"]

    return df


def pivot_df(df):
    pivoted_df = df.pivot_table(index=['end_date', 'year', 'ticker', 'form'],
                                             columns='type',
                                             values='val',
                                             aggfunc='sum')

    pivoted_df = pivoted_df.reset_index()

    return pivoted_df


def filtering_df(df):
    # Filtering for the relevant columns
    df = df.loc[:, columns_to_filter]
    # Filtering for records from 2008
    df = df[df["year"] >= 2008]
    # Dropping duplicates
    df.drop_duplicates(inplace=True)
    return df

def impute_feature_engineering(df):
    # Handling NaN values
    df.iloc[:,4:] = imputer.transform(df.iloc[:,4:])
    # Scaling values
    df.iloc[:, 4:] = scaler.transform(df.iloc[:, 4:])
    # Feature Selection
    df.drop(["EarningsPerShareDiluted", "LiabilitiesAndStockholdersEquity"], axis=1, inplace=True)
    return df

def running_the_model(df):
    X = df.iloc[:, 4:]
    y_pred = model.predict(X)
    df["anomaly"] = y_pred
    return df

def print_anomaly_periods(df):
    result_df = df[df["anomaly"]==1]
    result_list = result_df["year"].unique().tolist()
    result_list = [x+11 for x in result_list]
    return result_list

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


    ticker = input("\nPlace your ticker here: ")

    print(f"\nChecking if we have ticker {ticker} in our records...\n")

    # getting the existent tickers in our records
    existent_tickers = existent_tickers()

    # Checking if the ticker selected is in our records
    if is_ticker_available(ticker, existent_tickers):

        # Pulling data from s3
        query_df = pull_data_for_ticker(ticker)

        # Preprocessing
        query_df = preprocessing_df(query_df)

        # Pivot query_df
        pivoted_df = pivot_df(query_df)

        # Filtering
        filtered_df = filtering_df(pivoted_df)

        # Feature Engineering
        df = impute_feature_engineering(filtered_df)

        # Running the model on top
        df = running_the_model(df)

        # Final Output
        print(print_anomaly_periods(df))

