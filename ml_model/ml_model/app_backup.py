from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pandas as pd
import joblib
import shap


# Create FastAPI application
app = FastAPI(title="PayShield AI API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load ML model
model = joblib.load("fraud_model_tuned.pkl")
threshold = joblib.load("best_threshold.pkl")

# Create SHAP explainer
explainer = shap.TreeExplainer(model)


# Transaction input format

class Transaction(BaseModel):
    transaction_amount: float = Field(gt=0)
    transaction_hour: int = Field(ge=0, le=23)
    transaction_count_24h: int = Field(ge=0)
    is_new_receiver: int = Field(ge=0, le=1)
    failed_attempts: int = Field(ge=0)
    avg_transaction_amount: float = Field(gt=0)

# Home API
@app.get("/")
def home():
    return {
        "message": "Welcome to PayShield AI Fraud Detection API"
    }


# Prediction API
@app.post("/predict")
def predict(transaction: Transaction):

    amount = transaction.transaction_amount
    average = transaction.avg_transaction_amount

    deviation = abs(amount - average) / max(average, 1)

    data = pd.DataFrame([{
        "transaction_amount": amount,
        "transaction_hour": transaction.transaction_hour,
        "transaction_count_24h": transaction.transaction_count_24h,
        "is_new_receiver": transaction.is_new_receiver,
        "failed_attempts": transaction.failed_attempts,
        "avg_transaction_amount": average,
        "amount_deviation": deviation
    }])

    # Fraud score
    probability = model.predict_proba(data)[0][1]

    # Risk classification
    if probability >= 0.60:
        risk = "HIGH"
        prediction = "SUSPICIOUS"

    elif probability >= 0.30:
        risk = "MEDIUM"
        prediction = "REVIEW REQUIRED"

    else:
        risk = "LOW"
        prediction = "GENUINE"

    # SHAP explanation
    shap_exp = explainer(data)

    if len(shap_exp.values.shape) == 3:
        fraud_exp = shap_exp[:, :, 1]
    else:
        fraud_exp = shap_exp

    reasons = []

    for feature, value in zip(data.columns, fraud_exp.values[0]):

        if value > 0:
            reasons.append({
                "feature": feature,
                "impact": "increases fraud prediction",
                "shap_value": round(float(value), 4)
            })

    return {
        "fraud_score": round(float(probability * 100), 2),
        "prediction": prediction,
        "risk_level": risk,
        "threshold": threshold,
        "reasons": reasons,
        "warning": "Experimental model trained on synthetic data. Not proof of fraud."
    }
