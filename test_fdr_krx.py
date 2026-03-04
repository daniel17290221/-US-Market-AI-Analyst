import FinanceDataReader as fdr
import pandas as pd
import sys

print("Testing FDR StockListing('KRX')...")
try:
    df = fdr.StockListing('KRX')
    print(f"Success! Found {len(df)} stocks.")
    print(df.head())
except Exception as e:
    print(f"Failed: {e}")
