import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score
)

# 1. Load training data
df = pd.read_csv("dataset/train.csv")

X = df.drop("is_fraud", axis=1)
y = df["is_fraud"]

# 2. Split training and validation data
X_train, X_val, y_train, y_val = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("Training data:", X_train.shape)
print("Validation data:", X_val.shape)

# 3. Train Random Forest
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    class_weight="balanced",
    n_jobs=-1
)

print("\nTraining started...")
model.fit(X_train, y_train)
print("Training completed!")

# 4. Get fraud scores
y_prob = model.predict_proba(X_val)[:, 1]

# 5. Compare different thresholds
thresholds = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]

print("\nTHRESHOLD COMPARISON")
print("-" * 65)
print("Threshold | Precision | Recall | F1 Score")
print("-" * 65)

for threshold in thresholds:

    y_pred = (y_prob >= threshold).astype(int)

    precision = precision_score(
        y_val, y_pred, zero_division=0
    )

    recall = recall_score(
        y_val, y_pred, zero_division=0
    )

    f1 = f1_score(
        y_val, y_pred, zero_division=0
    )

    print(
        f"{threshold:.2f}      | "
        f"{precision:.3f}     | "
        f"{recall:.3f}  | "
        f"{f1:.3f}"
    )

print("\nThreshold testing completed!")
# 6. Find best threshold using validation F1-score

best_threshold = 0.0
best_f1 = 0.0

for threshold in thresholds:

    y_pred = (y_prob >= threshold).astype(int)

    f1 = f1_score(y_val, y_pred, zero_division=0)

    if f1 > best_f1:
        best_f1 = f1
        best_threshold = threshold

print("\nBest Threshold:", best_threshold)
print("Best Validation F1:", round(best_f1, 3))

# 7. Save model and threshold
import joblib

joblib.dump(model, "fraud_model_tuned.pkl")
joblib.dump(best_threshold, "best_threshold.pkl")

print("\nTuned model saved successfully!")
