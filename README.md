# wannabeModel

This is a project for Barcelona Technology School

Here we will save all the python and jupyter notebooks needed to:

1 - play with the EDGAR API

(initial_insights.ipynb, company_general_data.ipynb, apple_testing.ipynb, Apple_Accounts.csv)

2 - **sicCompaniesCsvGenerator.ipynb**: generates a CSV file for every top 10 industry in size containing a list of all the belonging companies

(needs companies_per_sic.csv, Company_Data.csv)

3 - **Ingestion Script (ingestion.py)**:
Extracts company JSON data by giving it a list of tickers.
Stores a JSON file for each company in the S3.


4 - **Processing Script (processor.py)**:
Reads the JSON data in the s3 bucket.
Creates a RDS table with columns: ticker, date, form, type, amount and Stores the data in an RDS database


5 - **Modelling Script (model.py)**:
Queries the db to extract required data.
Preprocesses the data.
Runs different models and evaluates their performance. 


(needs .env file that will not be committed to git)

