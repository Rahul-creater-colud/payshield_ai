import pandas as pd

df = pd.read_csv("dataset/transactions.csv")

print("Dataset Information:")
print(df.info())

print("\nMissing Values:")
print(df.isnull().sum())

print("\nDuplicate Rows:")
print(df.duplicated().sum())

print("\nFraud Distribution:")
print(df["is_fraud"].value_counts())

print("\nFraud Percentage:")
print(df["is_fraud"].value_counts(normalize=True) * 100)

print("\nStatistical Summary:")
print(df.describe())
