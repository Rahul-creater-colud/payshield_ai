"""Optional supplemental inference using the project's synthetic-trained model."""

from __future__ import annotations

import importlib
import logging
import math
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

from app.config import settings

logger = logging.getLogger(__name__)

FEATURE_NAMES = (
    "transaction_amount",
    "transaction_hour",
    "transaction_count_24h",
    "is_new_receiver",
    "failed_attempts",
    "avg_transaction_amount",
    "amount_deviation",
)

MODEL_NAME = "Experimental Random Forest"
TRAINING_DATA_LABEL = "Synthetic generated labels; not real UPI outcomes"


def _as_utc(value: datetime | str) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def build_transaction_features(
    amount: float,
    timestamp: datetime | str,
    previous_transactions: Iterable[Any],
    receiver_id: str,
    exclude_transaction_id: Optional[str] = None,
) -> tuple[dict[str, float | int], list[str]]:
    """Derive model inputs only from the submitted transaction and stored history."""
    input_timestamp = (
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if isinstance(timestamp, str)
        else timestamp
    )
    transaction_hour = input_timestamp.hour
    assessed_at = _as_utc(timestamp)
    history = []
    for transaction in previous_transactions:
        if (
            exclude_transaction_id
            and transaction.transaction_id == exclude_transaction_id
        ):
            continue
        try:
            transaction_time = _as_utc(transaction.timestamp)
        except (TypeError, ValueError):
            continue
        if transaction_time <= assessed_at:
            history.append((transaction, transaction_time))

    prior_sender_transactions = [
        transaction for transaction, _ in history if transaction.amount > 0
    ]
    recent_transaction_count = sum(
        transaction_time >= assessed_at - timedelta(hours=24)
        for _, transaction_time in history
    )
    average_amount = (
        sum(transaction.amount for transaction in prior_sender_transactions)
        / len(prior_sender_transactions)
        if prior_sender_transactions
        else amount
    )
    known_receivers = {
        transaction.receiver_id.strip().lower()
        for transaction, _ in history
    }

    assumptions = ["Failed-attempt history is not stored; the model input is set to 0."]
    if not prior_sender_transactions:
        assumptions.append(
            "No prior sender transactions were recorded; this transaction's amount "
            "is used as a neutral average-amount baseline."
        )

    return {
        "transaction_amount": float(amount),
        "transaction_hour": transaction_hour,
        "transaction_count_24h": recent_transaction_count,
        "is_new_receiver": int(receiver_id.strip().lower() not in known_receivers),
        "failed_attempts": 0,
        "avg_transaction_amount": float(average_amount),
        "amount_deviation": abs(amount - average_amount) / max(average_amount, 1),
    }, assumptions


class ExperimentalMLModelService:
    """Loads only the configured local artifact and reports inference availability."""

    def __init__(self) -> None:
        self._model: Any = None
        self._threshold: Optional[float] = None
        self._model_name = MODEL_NAME
        self._training_data_label = TRAINING_DATA_LABEL
        self._loaded = False
        self._state: dict[str, Any] = {}
        self._lock = threading.Lock()

    def _artifact_directory(self) -> Path:
        if settings.ML_MODEL_DIR:
            return Path(settings.ML_MODEL_DIR).expanduser()
        return Path(__file__).resolve().parents[3] / "ml_model" / "ml_model"

    def _load_artifacts(self) -> tuple[Any, float]:
        directory = self._artifact_directory()
        import joblib
        importlib.import_module("pandas")

        artifact_directory = directory / "artifacts"
        packaged_model_path = artifact_directory / "best_model.joblib"
        packaged_threshold_path = artifact_directory / "best_threshold.joblib"
        legacy_model_path = directory / "fraud_model_tuned.pkl"
        legacy_threshold_path = directory / "best_threshold.pkl"

        # These are trusted, locally configured project artifacts, never user uploads.
        if packaged_model_path.is_file() or packaged_threshold_path.is_file():
            if not packaged_model_path.is_file() or not packaged_threshold_path.is_file():
                raise FileNotFoundError("The packaged model and threshold must both exist.")
            package = joblib.load(packaged_model_path)
            if not isinstance(package, dict):
                raise ValueError("The packaged model artifact has an invalid format.")
            model = package.get("pipeline")
            feature_names = package.get("feature_names")
            if tuple(feature_names or ()) != FEATURE_NAMES:
                raise ValueError("The packaged artifact feature schema does not match inference.")
            self._model_name = str(package.get("model_name") or MODEL_NAME)
            self._training_data_label = str(
                package.get("training_data") or TRAINING_DATA_LABEL
            )
            threshold = float(joblib.load(packaged_threshold_path))
        elif legacy_model_path.is_file() and legacy_threshold_path.is_file():
            model = joblib.load(legacy_model_path)
            threshold = float(joblib.load(legacy_threshold_path))
        else:
            raise FileNotFoundError(
                "No complete packaged or legacy model artifacts were found."
            )

        if not math.isfinite(threshold) or not 0 <= threshold <= 1:
            raise ValueError("The model threshold must be between 0 and 1.")
        if getattr(model, "n_features_in_", None) != len(FEATURE_NAMES):
            raise ValueError("The model feature count does not match the inference schema.")
        model_features = getattr(model, "feature_names_in_", None)
        if model_features is not None and tuple(model_features) != FEATURE_NAMES:
            raise ValueError("The model feature order does not match the inference schema.")
        if 1 not in getattr(model, "classes_", ()):
            raise ValueError("The model does not expose a fraud class.")
        return model, threshold

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            if not settings.ML_MODEL_ENABLED:
                self._state = {
                    "status": "disabled",
                    "message": "Experimental ML inference is disabled by configuration.",
                }
            else:
                try:
                    self._model, self._threshold = self._load_artifacts()
                    self._state = {
                        "status": "active",
                        "message": "Supplemental model estimate is available.",
                    }
                except FileNotFoundError:
                    self._state = {
                        "status": "unavailable",
                        "message": "Model artifacts are missing from the configured model directory.",
                    }
                    logger.warning("%s", self._state["message"])
                except ImportError:
                    self._state = {
                        "status": "unavailable",
                        "message": "Model dependencies are missing; install backend/requirements.txt.",
                    }
                    logger.exception("Could not import dependencies for the experimental ML model.")
                except Exception:
                    self._state = {
                        "status": "unavailable",
                        "message": "Model artifacts could not be loaded or did not match the expected schema.",
                    }
                    logger.exception("Could not load the configured experimental ML model.")
            self._loaded = True

    def status(self) -> dict[str, Any]:
        self._ensure_loaded()
        return {
            "status": self._state["status"],
            "model_name": self._model_name,
            "training_data": self._training_data_label,
            "affects_final_score": False,
            "message": self._state["message"],
        }

    def predict(
        self,
        features: dict[str, float | int],
        feature_assumptions: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        self._ensure_loaded()
        result = {
            **self.status(),
            "probability": None,
            "threshold": None,
            "prediction": None,
            "feature_assumptions": feature_assumptions or [],
        }
        if self._state["status"] != "active":
            return result

        try:
            import pandas as pd

            values = [float(features[name]) for name in FEATURE_NAMES]
            if not all(math.isfinite(value) for value in values):
                raise ValueError("Model input features must be finite numbers.")
            probabilities = self._model.predict_proba(
                pd.DataFrame([values], columns=FEATURE_NAMES)
            )[0]
            fraud_class_index = list(self._model.classes_).index(1)
            probability = float(probabilities[fraud_class_index])
            if not math.isfinite(probability) or not 0 <= probability <= 1:
                raise ValueError("The model returned an invalid probability.")
        except Exception:
            logger.exception("Experimental ML inference failed.")
            result.update(
                status="error",
                message="Model inference failed; see backend logs. Heuristic assessment is unchanged.",
            )
            return result

        result.update(
            probability=probability,
            threshold=self._threshold,
            prediction="SUSPICIOUS" if probability >= self._threshold else "NOT_FLAGGED",
        )
        return result


ml_model_service = ExperimentalMLModelService()
