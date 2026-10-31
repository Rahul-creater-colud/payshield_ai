from pathlib import Path

import pandas as pd
import numpy as np

np.random.seed(42)

n = 10000

amount = np.random.lognormal(7, 1, n).round(2)
hour = np.random.randint(0, 24, n)
transaction_count = np.random.randint(1, 15, n)

new_receiver = np.random.choice(
    [0, 1], n, p=[0.75, 0.25]
)

failed_attempts = np.random.poisson(0.3, n)

avg_amount = np.random.lognormal(6.5, 0.8, n).round(2)

amount_deviation = (
    np.abs(amount - avg_amount) / (avg_amount + 1)
).round(2)

risk = (
    (amount_deviation > 3) * 2.0
    + (hour <= 5) * 0.8
    + (transaction_count >= 10) * 1.0
    + (new_receiver == 1) * 0.8
    + (failed_attempts >= 2) * 1.0
)

probability = 1 / (1 + np.exp(-(risk - 3.5)))

is_fraud = np.random.binomial(1, probability)

df = pd.DataFrame({
    "transaction_amount": amount,
    "transaction_hour": hour,
    "transaction_count_24h": transaction_count,
    "is_new_receiver": new_receiver,
    "failed_attempts": failed_attempts,
    "avg_transaction_amount": avg_amount,
    "amount_deviation": amount_deviation,
    "is_fraud": is_fraud
})

dataset_path = Path(__file__).resolve().parent / "dataset" / "transactions.csv"
dataset_path.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(dataset_path, index=False)

print("Dataset generated successfully!")
print("\nFirst 5 rows:")
print(df.head())

print("\nDataset shape:")
print(df.shape)

print("\nFraud distribution:")
print(df["is_fraud"].value_counts())