import pickle

imputer = pickle.load(open('../Model/imputer.pkl', 'rb'))
scaler = pickle.load(open('../Model/scaler.pkl', 'rb'))
model = pickle.load(open('../Model/best_model.pkl', 'rb'))


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

df.loc[:columns_to_filter]