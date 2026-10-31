from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pandas as pd
import joblib
import shap

app = FastAPI(title="PayShield AI API")

# React frontend connection
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

# Load trained model and threshold
model = joblib.load("fraud_model_tuned.pkl")
threshold = float(joblib.load("best_threshold.pkl"))

explainer = shap.TreeExplainer(model)


class Transaction(BaseModel):
    transaction_amount: float = Field(gt=0)
    transaction_hour: int = Field(ge=0, le=23)
    transaction_count_24h: int = Field(ge=0)
    is_new_receiver: int = Field(ge=0, le=1)
    failed_attempts: int = Field(ge=0)
    avg_transaction_amount: float = Field(gt=0)


@app.get("/")
def home():
    return {
        "message": "PayShield AI API is running",
        "model": "Random Forest Tuned",
        "threshold": threshold
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


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

    # Get fraud-class probability
    fraud_index = list(model.classes_).index(1)
    score = float(model.predict_proba(data)[0][fraud_index])

    # Apply validation-selected threshold
    is_suspicious = score >= threshold

    risk = "HIGH" if is_suspicious else "LOW"
    prediction = "SUSPICIOUS" if is_suspicious else "NOT FLAGGED"

    # SHAP explanation
    shap_exp = explainer(data)

    if len(shap_exp.values.shape) == 3:
        fraud_exp = shap_exp[:, :, fraud_index]
    else:
        fraud_exp = shap_exp

    reasons = []

    for feature, value in zip(data.columns, fraud_exp.values[0]):
        reasons.append({
            "feature": feature,
            "impact": (
                "increases fraud prediction"
                if value > 0
                else "decreases fraud prediction"
            ),
            "shap_value": round(float(value), 4)
        })

    reasons.sort(
        key=lambda item: abs(item["shap_value"]),
        reverse=True
    )

    return {
        "model_score_percent": round(score * 100, 2),
        "prediction": prediction,
        "risk_level": risk,
        "selected_threshold": threshold,
        "reasons": reasons,
        "warning": (
            "Experimental model trained on synthetic data. "
            "A suspicious prediction is not proof of fraud."
        )
    }
