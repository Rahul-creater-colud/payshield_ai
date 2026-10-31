import pandas as pd
import joblib
import shap
import matplotlib.pyplot as plt

# 1. Load trained model
model = joblib.load("fraud_model.pkl")

# 2. Load test dataset
df = pd.read_csv("dataset/test.csv")

X_test = df.drop("is_fraud", axis=1)

# 3. Select one transaction
sample = X_test.iloc[[0]]

# 4. Create SHAP explainer
explainer = shap.TreeExplainer(model)

# 5. Calculate SHAP values
shap_exp = explainer(sample)

# 6. Select fraud class (class 1)
if len(shap_exp.values.shape) == 3:
    fraud_exp = shap_exp[:, :, 1]
else:
    fraud_exp = shap_exp

# 7. Display prediction
prediction = model.predict(sample)[0]
probability = model.predict_proba(sample)[0][1]

print("\nTransaction Details:")
print(sample)

print("\nPrediction:", prediction)
print("Fraud Probability:", round(probability * 100, 2), "%")

# 8. Display feature contributions
values = fraud_exp.values[0]

result = pd.DataFrame({
    "Feature": sample.columns,
    "SHAP Value": values
})

result["Impact"] = result["SHAP Value"].apply(
    lambda x: "Increases fraud prediction"
    if x > 0 else "Decreases fraud prediction"
)

result = result.reindex(
    result["SHAP Value"].abs().sort_values(
        ascending=False
    ).index
)

print("\nSHAP Explanation:")
print(result)

# 9. Generate SHAP waterfall plot
shap.plots.waterfall(fraud_exp[0], show=False)

plt.tight_layout()
plt.savefig("shap_explanation.png")

print("\nSHAP explanation saved successfully!")
