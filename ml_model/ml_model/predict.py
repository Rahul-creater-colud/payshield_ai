import joblib
import pandas as pd
import shap
# Load trained model
model = joblib.load("fraud_model_tuned.pkl")

# Load best threshold
threshold = joblib.load("best_threshold.pkl")

# Create SHAP explainer
explainer = shap.TreeExplainer(model)

print("PayShield AI Fraud Detection System")
print("-----------------------------------")

# Take transaction details from user
amount = float(input("Enter transaction amount: "))
hour = int(input("Enter transaction hour (0-23): "))
count = int(input("Transactions in last 24 hours: "))
new_receiver = int(input("Is receiver new? (1=Yes, 0=No): "))
failed = int(input("Failed attempts: "))
average = float(input("Average transaction amount: "))

# Calculate amount deviation
deviation = abs(amount - average) / max(average, 1)

# Prepare transaction data
data = pd.DataFrame([{
    "transaction_amount": amount,
    "transaction_hour": hour,
    "transaction_count_24h": count,
    "is_new_receiver": new_receiver,
    "failed_attempts": failed,
    "avg_transaction_amount": average,
    "amount_deviation": deviation
}])

# Predict fraud score
fraud_probability = model.predict_proba(data)[0][1]

# Generate SHAP explanation
shap_exp = explainer(data)

# Get fraud class explanation
if len(shap_exp.values.shape) == 3:
    fraud_exp = shap_exp[:, :, 1]
else:
    fraud_exp = shap_exp

# Create explanation table
explanation = pd.DataFrame({
    "Feature": data.columns,
    "SHAP Value": fraud_exp.values[0]
})

explanation = explanation.sort_values(
    by="SHAP Value",
    ascending=False
)

print("\n----- WHY THIS TRANSACTION IS SUSPICIOUS -----")

for _, row in explanation.iterrows():

    if row["SHAP Value"] > 0:
        print("Increases fraud score:", row["Feature"])

    elif row["SHAP Value"] < 0:
        print("Decreases fraud score:", row["Feature"])

# Apply threshold and classify risk

if fraud_probability >= 0.60:
    prediction = "SUSPICIOUS"
    risk = "HIGH"

elif fraud_probability >= 0.30:
    prediction = "REVIEW REQUIRED"
    risk = "MEDIUM"

else:
    prediction = "GENUINE"
    risk = "LOW"


# Display result
print("\n----- PAYSHIELD AI RESULT -----")
print("Fraud Score:", round(fraud_probability * 100, 2), "%")
print("Prediction:", prediction)
print("Risk Level:", risk)
