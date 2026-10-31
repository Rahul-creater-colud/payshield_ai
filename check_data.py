import pandas as pd

base = "ml_model/ml_model/"
paths = [
    base + "data/synthetic_indian_upi_fraud_data.csv",
    base + "dataset/transactions.csv",
]

for p in paths:
    df = pd.read_csv(p)
    print("\n" + "=" * 60)
    print("File:", p)
    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())
    print(df.head(3).to_string())
    for c in df.columns:
        if "fraud" in c.lower() or "label" in c.lower():
            print("\nLabel column:", c)
            print(df[c].value_counts())
