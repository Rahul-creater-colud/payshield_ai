import pandas as pd

from sklearn.model_selection import train_test_split

# 1. Load dataset
df = pd.read_csv("dataset/transactions.csv")

print("Original Dataset:", df.shape)

# 2. Remove duplicate rows
df = df.drop_duplicates()

# 3. Handle missing values
df = df.dropna()

# 4. Separate features and target
X = df.drop("is_fraud", axis=1)
y = df["is_fraud"]

print("\nFeatures:")
print(X.columns.tolist())

print("\nTarget:")
print(y.value_counts())

# 5. Split data into training and testing
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

# 6. Save training and testing datasets
train_data = X_train.copy()
train_data["is_fraud"] = y_train

test_data = X_test.copy()
test_data["is_fraud"] = y_test

train_data.to_csv("dataset/train.csv", index=False)
test_data.to_csv("dataset/test.csv", index=False)

# 7. Display results
print("\nPreprocessing Completed!")

print("Training Data:", X_train.shape)
print("Testing Data:", X_test.shape)

print("\nTraining Fraud Distribution:")
print(y_train.value_counts())

print("\nTesting Fraud Distribution:")
print(y_test.value_counts())
