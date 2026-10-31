import pandas as pd
import joblib

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score
)

# Load tuned model and threshold
model = joblib.load("fraud_model_tuned.pkl")
threshold = joblib.load("best_threshold.pkl")

# Load untouched test dataset
df = pd.read_csv("dataset/test.csv")

X_test = df.drop("is_fraud", axis=1)
y_test = df["is_fraud"]

# Predict fraud scores
y_prob = model.predict_proba(X_test)[:, 1]

# Apply tuned threshold
y_pred = (y_prob >= threshold).astype(int)

# Evaluate model
print("Selected Threshold:", threshold)

print("\nAccuracy:")
print(accuracy_score(y_test, y_pred))

print("\nPrecision:")
print(precision_score(y_test, y_pred, zero_division=0))

print("\nRecall:")
print(recall_score(y_test, y_pred, zero_division=0))

print("\nF1 Score:")
print(f1_score(y_test, y_pred, zero_division=0))

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nFinal Evaluation Completed!")
