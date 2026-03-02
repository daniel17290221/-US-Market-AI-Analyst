import FinanceDataReader as fdr
import pandas as pd
import json

def test():
    try:
        print("Testing fdr.StockListing('KRX')...")
        df = fdr.StockListing('KRX')
        print(f"Success! Found {len(df)} rows.")
        print(df.head())
        
        print("\nTesting fdr.DataReader('KS11')...")
        df_idx = fdr.DataReader('KS11').tail(5)
        print(f"Success! Index data:\n{df_idx}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test()
