# wannabeModel

This is a project for Barcelona Technology School.

This repository is divided into two parts:
1. The code that creates the anomaly detection model on financial reports.
2. The code that web scrapes data from HTML financial reports and financial news.

## Anomaly_Model
### Initial Data Flow:
- Extracts financial information from EDGAR APIs and replicates the data in an AWS S3 bucket.
- Processes the data in AWS and appends it to AWS RDS.

### Notebooks:
- Queries the RDS for anomalous tickers and labels the dataset with a binary target column.
- Performs EDA (Exploratory Data Analysis) on the dataset.
- Feature engineering on the dataset.
- Tries different pairs of data preprocessing techniques and models, evaluating which one scores higher.

## LLM
- Web scrapes data from HTML reports and integrates an LLAMA3 model to summarize reports.
- Web scrapes financial news and performs sentiment analysis.


## Project Structure

Directory Structure

```bash
wannabeModel/
├── Anomaly_Model/ # Contains the anomaly detection model scripts, data, and results
├── LLM/ # Contains the language model scripts, web scraping scripts, and sentiment analysis scripts
├── .env-example # Example environment variables file
├── .gitignore # Git ignore rules
├── README.md # Project documentation
├── requirements.txt # Python dependencies
```

### Directories and Key Files

#### Anomaly_Model/
Contains the scripts for the anomaly detection model.

- `requirements.txt`: Lists the Python dependencies for the anomaly model.

#### LLM/
Contains the language model script, web scraping scripts, and sentiment analysis script.

#### .env-example
An example environment variables file. Copy this to `.env` and fill in the required variables to configure your local environment.

#### .gitignore
Specifies files and directories to be ignored by git.

#### README.md
The documentation file you are currently reading.

#### requirements.txt
Lists all the dependencies required to run the project.

## Setup

1. **Clone the repository to your local computer:**

```sh
   git clone https://github.com/FinancyAI/wannabeModel.git
```

2  **Create .env file for AWS access**

```bash
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
```

3  **Download necessary dependencies**:

```sh
    pip3 install -r requirements.txt
