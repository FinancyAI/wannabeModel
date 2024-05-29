# wannabeModel

This is a project for Barcelona Technology School

Here we will save all the python and jupyter notebooks needed to:

1 - play with the EDGAR API

(initial_insights.ipynb, company_general_data.ipynb, apple_testing.ipynb, Apple_Accounts.csv)

2 - **sicCompaniesCsvGenerator.ipynb**: generates a CSV file for every top 10 industry in size containing a list of all the belonging companies

(needs companies_per_sic.csv, Company_Data.csv)

3 - **extractor.py**: extracts cik (company) data from the API based on a sic (industry) provided, organize it and store it as a CSV.
The reason why we decided to organize the data can be seen on the FinancyEDA.ipynb.

4 - **uploader.py**: uploads a csv file, that contains financial statement data about all the companies in a certain industry, to an s3 bucket. This file receives the path_to_file to the .env file as a parameter, where we will store the AWS credentials

(needs .env file that will not be committed to git)

