# wannabeModel

This is a project for Barcelona Technology School.

This repository performs various tasks related to anomaly detection for financial reports of US publicly traded companies. Some of the tasks are the following:

- Extracts financial information from EDGAR APIs and replicates the data in an AWS S3 bucket.
- Processes the data in aws and appends it to RDS
- Trains a model to detect anomalies from financial reports.

- Web scrapes from two data sources, performs sentiment analysis, and integrates an LLAMA3 model to summarize reports.

## Project Structure

Directory Structure

├── .idea/ # Project settings
├── Anomaly_Model/ # Contains the anomaly detection model scripts, data, and results
├── LLM/ # Contains the language model data
├── .DS_Store # MacOS system file (can be ignored)
├── .env-example # Example environment variables file
├── .gitignore # Git ignore rules
├── README.md # Project documentation
├── requirements.txt # Python dependencies

## Directories and Key Files

### .idea/
Project settings for your IDE (e.g., PyCharm). Typically, this can be ignored by other users.

### Anomaly_Model/
Contains the scripts for the anomaly detection model.

- `requirements.txt`: Lists the Python dependencies for the anomaly model.

### LLM/
Contains the language model script, web scraping scripts, and sentiment analysis script.

### .DS_Store
A system file created by macOS. Can be ignored.

### .env-example
An example environment variables file. Copy this to `.env` and fill in the required variables to configure your local environment.

### .gitignore
Specifies files and directories to be ignored by git.

### README.md
The documentation file you are currently reading.

### requirements.txt
Lists all the dependencies required to run the project.

# Setup

1 - Clone the repository in your local computer. 

git clone https://github.com/FinancyAI/wannabeModel.git

2 - Create .env file for AWS access

# AWS Credentials
[default]
aws_access_key_id= {YOUR-KEY-ID}
aws_secret_access_key= {YOUR-ACCESS-KEY}
aws_session_token= {YOUR-SESSION-TOKEN}

# AWS DB connection credentials
db_name={db_name}
db_username={db_username}
db_password={db_password}
db_port={db_port}
db_host={db_host}

3 - **Download necessary dependencies.**:
pip install -r requirements.txt
