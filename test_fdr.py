import FinanceDataReader as fdr
print("FDR imported")
df = fdr.StockListing('KRX')
print("Stock listing fetched")
print(df.head())
