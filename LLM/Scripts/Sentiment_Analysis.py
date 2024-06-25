import pandas as pd
import nltk
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from transformers import BertTokenizer, BertForSequenceClassification
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import torch

# Ensure you have the necessary NLTK data files
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
nltk.download('vader_lexicon')

# Load FinBert model and tokenizer
model_name = 'yiyanghkust/finbert-tone'
tokenizer = BertTokenizer.from_pretrained(model_name)
model = BertForSequenceClassification.from_pretrained(model_name)

# Load VADER sentiment analyzer
vader_analyzer = SentimentIntensityAnalyzer()

# Sample DataFrame
df = pd.read_csv("output.csv")

lemmatizer = WordNetLemmatizer()

def get_wordnet_pos(word):
    """Map POS tag to first character lemmatize() accepts."""
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}
    return tag_dict.get(tag, wordnet.NOUN)

def lemmatize_text(text):
    """Lemmatize the text."""
    words = nltk.word_tokenize(text)
    lemmatized_words = [lemmatizer.lemmatize(word, get_wordnet_pos(word)) for word in words]
    return ' '.join(lemmatized_words)

# Apply lemmatization to the news text
df['lemmatized_texts'] = df['Body'].apply(lemmatize_text)

# Function to get sentiment scores using FinBert
def get_finbert_scores(text):
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=512)
    outputs = model(**inputs)
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
    return probs.detach().numpy()[0]

# Apply sentiment analysis using FinBert and ensure the scores are numeric
scores_df = df['lemmatized_texts'].apply(lambda x: pd.Series(get_finbert_scores(x))).astype(float)
scores_df.columns = ['negative_score', 'neutral_score', 'positive_score']
df = pd.concat([df, scores_df], axis=1)

# Function to determine overall sentiment based on the highest score
def determine_sentiment(row):
    scores = row[['negative_score', 'neutral_score', 'positive_score']]
    if row['negative_score'] > row['positive_score'] and row['negative_score'] > row['neutral_score']:
        return 'negative'
    elif row['positive_score'] > row['negative_score'] and row['positive_score'] > row['neutral_score']:
        return 'negative'
    else:
        return 'neutral'

# Apply the sentiment determination function
df['sentiment_category'] = df.apply(determine_sentiment, axis=1)

# Function to get compound score using VADER
def get_compound_score(text):
    return vader_analyzer.polarity_scores(text)['compound']

# Apply VADER compound score
df['compound_score'] = df['lemmatized_texts'].apply(get_compound_score)

# Function to determine sentiment based on compound score
def determine_compound_sentiment(compound_score):
    if compound_score >= 0.05:
        return 'positive'
    elif compound_score <= -0.05:
        return 'negative'
    else:
        return 'neutral'

# Apply the compound sentiment determination function
df['compound_sentiment_category'] = df['compound_score'].apply(determine_compound_sentiment)

# Show the DataFrame with the scores and overall sentiment
print(df)

# Optional: Create a pipeline for vectorization and transformation if needed
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer()),
])

# Transform the lemmatized texts using the pipeline
tfidf_matrix = pipeline.fit_transform(df['lemmatized_texts'])

# To view the TF-IDF matrix
tfidf_df = pd.DataFrame(tfidf_matrix.toarray(), columns=pipeline['tfidf'].get_feature_names_out())

# Display the TF-IDF DataFrame
print(tfidf_df)

# Saving Data
df.to_csv("sentiment_data.csv", index=False)
tfidf_df.to_csv("tfidf_data.csv", index=False)
