import pandas as pd

df = pd.read_csv("data/monthly_spending_dataset_2020_2025.csv")
print("Columns:", list(df.columns))
print(df.head(3))