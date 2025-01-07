import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt

def main():
    companies = ['COALINDIA', 'RELIANCE', 'ICICIBANK', 'TITAN', 'ITC', 'WIPRO', 'TCS', 'TATAMOTORS', 'HDFCLIFE', 'INFY']
    stock_data = {}
    
    # Download and preprocess data
    for company in companies:
        df = yf.download(tickers=company + '.NS', period='6mo', interval='1d')
        df['Return'] = df['Close'].pct_change()
        df['SMA_5'] = df['Close'].rolling(window=5).mean()
        df['SMA_10'] = df['Close'].rolling(window=10).mean()
        df['Volatility'] = df['Return'].rolling(window=5).std()
        df = df.dropna()
        stock_data[company] = df
    
    results = []
    
    # Train a model for each company
    for company, df in stock_data.items():
        features = df[['SMA_5', 'SMA_10', 'Volatility']]
        target = df['Return']
        
        X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        predicted_return = model.predict(X_test).mean()
        risk = df['Return'].std()
        
        results.append({'Company': company, 'Predicted_Return': predicted_return, 'Risk': risk})
    
    # Create DataFrame and rank companies
    result_df = pd.DataFrame(results)
    result_df = result_df.sort_values(by=['Predicted_Return', 'Risk'], ascending=[False, True])
    
    # Select top 5 companies
    top_companies = result_df.head(5)
    print(top_companies)
    
    # Allocate weights based on predicted return and risk
    split = []
    for i in range(5):
        split.append(top_companies.iloc[i]['Predicted_Return'] * (1 - top_companies.iloc[i]['Risk']))
    total = sum(split)
    split = [w / total for w in split]
    
    return list(top_companies['Company']), split

if __name__ == '__main__':
    companies, split = main()
    print('Selected Companies:', companies)
    print('Allocation Split:', split)
