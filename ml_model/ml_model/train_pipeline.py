"""Reproducibly compare fraud classifiers on the synthetic project dataset.

Metrics produced by this script measure agreement with generated labels only.
They are not evidence of performance on real UPI transactions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 42
TARGET = "is_fraud"
FEATURES = [
    "transaction_amount",
    "transaction_hour",
    "transaction_count_24h",
    "is_new_receiver",
    "failed_attempts",
    "avg_transaction_amount",
    "amount_deviation",
]


def _read_dataset(path: Path) -> tuple[pd.DataFrame, pd.Series, dict[str, Any]]:
    raw_bytes = path.read_bytes()
    frame = pd.read_csv(path)
    if TARGET not in frame.columns:
        raise ValueError(f"Dataset must contain target column {TARGET!r}.")
    missing_features = sorted(set(FEATURES) - set(frame.columns))
    if missing_features:
        raise ValueError(f"Dataset is missing required features: {missing_features}")

    frame = frame[FEATURES + [TARGET]].copy()
    frame = frame.dropna(subset=[TARGET])
    frame = frame.drop_duplicates()
    labels = frame.pop(TARGET)
    if not labels.isin([0, 1]).all():
        raise ValueError("The target must contain binary 0/1 labels.")
    labels = labels.astype("int8")

    for column in FEATURES:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame.loc[~np.isfinite(frame[column]), column] = np.nan

    if labels.nunique() != 2 or labels.value_counts().min() < 5:
        raise ValueError("At least five examples of each class are required.")
    info = {
        "sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "rows_after_target_cleanup_and_deduplication": int(len(frame)),
        "source_missing_feature_values": int(frame.isna().sum().sum()),
        "class_counts": {str(k): int(v) for k, v in labels.value_counts().sort_index().items()},
    }
    return frame, labels, info


def _candidate_models() -> dict[str, Pipeline]:
    return {
        "logistic_regression_balanced": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    LogisticRegression(
                        class_weight="balanced",
                        max_iter=2000,
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
        "random_forest_balanced": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=300,
                        min_samples_leaf=2,
                        class_weight="balanced_subsample",
                        random_state=RANDOM_STATE,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }


def _select_threshold(labels: pd.Series, probabilities: np.ndarray) -> dict[str, float]:
    thresholds = np.unique(np.concatenate(([0.0, 0.5, 1.0], probabilities)))
    best: tuple[float, float, float] | None = None
    for threshold in thresholds:
        predicted = probabilities >= threshold
        precision = precision_score(labels, predicted, zero_division=0)
        recall = recall_score(labels, predicted, zero_division=0)
        f1 = f1_score(labels, predicted, zero_division=0)
        candidate = (float(f1), float(precision), float(threshold))
        if best is None or candidate > best:
            best = candidate
    assert best is not None
    return {"threshold": best[2], "precision": best[1], "f1": best[0]}


def _metrics(labels: pd.Series, probabilities: np.ndarray, threshold: float) -> dict[str, Any]:
    predicted = probabilities >= threshold
    matrix = confusion_matrix(labels, predicted, labels=[0, 1])
    return {
        "precision": float(precision_score(labels, predicted, zero_division=0)),
        "recall": float(recall_score(labels, predicted, zero_division=0)),
        "f1": float(f1_score(labels, predicted, zero_division=0)),
        "pr_auc_average_precision": float(average_precision_score(labels, probabilities)),
        "confusion_matrix_labels": ["not_fraud", "synthetic_fraud"],
        "confusion_matrix": matrix.tolist(),
        "threshold": float(threshold),
        "support": {
            "not_fraud": int((labels == 0).sum()),
            "synthetic_fraud": int((labels == 1).sum()),
        },
    }


def train(dataset: Path, output_dir: Path) -> dict[str, Any]:
    features, labels, dataset_info = _read_dataset(dataset)
    development_x, holdout_x, development_y, holdout_y = train_test_split(
        features,
        labels,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=labels,
    )
    train_x, validation_x, train_y, validation_y = train_test_split(
        development_x,
        development_y,
        test_size=0.25,
        random_state=RANDOM_STATE + 1,
        stratify=development_y,
    )

    comparisons: dict[str, Any] = {}
    for name, candidate in _candidate_models().items():
        candidate.fit(train_x, train_y)
        validation_probabilities = candidate.predict_proba(validation_x)[:, 1]
        threshold_choice = _select_threshold(validation_y, validation_probabilities)
        comparisons[name] = {
            "validation_pr_auc_average_precision": float(
                average_precision_score(validation_y, validation_probabilities)
            ),
            "validation_threshold": threshold_choice,
        }

    selected_name = max(
        comparisons,
        key=lambda name: (
            comparisons[name]["validation_pr_auc_average_precision"],
            comparisons[name]["validation_threshold"]["f1"],
            name,
        ),
    )
    threshold = comparisons[selected_name]["validation_threshold"]["threshold"]

    final_model = _candidate_models()[selected_name]
    final_model.fit(development_x, development_y)
    holdout_probabilities = final_model.predict_proba(holdout_x)[:, 1]
    holdout_metrics = _metrics(holdout_y, holdout_probabilities, threshold)

    output_dir.mkdir(parents=True, exist_ok=True)
    artifact = {
        "pipeline": final_model,
        "model_name": selected_name,
        "feature_names": FEATURES,
        "training_data": "Synthetically generated labels; not real UPI outcomes",
        "random_state": RANDOM_STATE,
        "sklearn_version": sklearn.__version__,
    }
    temporary_model = output_dir / "best_model.joblib.tmp"
    joblib.dump(artifact, temporary_model, compress=3)
    temporary_model.replace(output_dir / "best_model.joblib")
    temporary_threshold = output_dir / "best_threshold.joblib.tmp"
    joblib.dump(float(threshold), temporary_threshold)
    temporary_threshold.replace(output_dir / "best_threshold.joblib")

    report = {
        "dataset": dataset.name,
        "dataset_provenance": (
            "Generated by create_dataset.py using a hand-authored risk formula and "
            "randomly sampled labels; no real payment outcomes are present."
        ),
        "dataset_sha256": dataset_info["sha256"],
        "dataset_info": dataset_info,
        "split": {
            "method": "stratified train/validation/holdout split",
            "random_state": RANDOM_STATE,
            "rows": {
                "training": int(len(train_y)),
                "validation": int(len(validation_y)),
                "development_refit": int(len(development_y)),
                "untouched_holdout": int(len(holdout_y)),
            },
        },
        "imbalance_handling": "class_weight=balanced for logistic regression; balanced_subsample for random forest",
        "missing_values": "Median imputation fitted within each training pipeline; no source feature values are missing.",
        "model_comparison": comparisons,
        "selected_model": selected_name,
        "selected_threshold_from_validation": threshold,
        "untouched_holdout_metrics": holdout_metrics,
        "sklearn_version": sklearn.__version__,
        "random_state": RANDOM_STATE,
        "warning": (
            "All reported metrics evaluate agreement with synthetic labels from a "
            "known rule generator. They do not measure real-world fraud detection."
        ),
    }
    output_report = output_dir / "evaluation.json"
    temporary_report = output_dir / "evaluation.json.tmp"
    temporary_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    temporary_report.replace(output_report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    default_dir = Path(__file__).resolve().parent
    parser.add_argument("--dataset", type=Path, default=default_dir / "dataset" / "transactions.csv")
    parser.add_argument("--output-dir", type=Path, default=default_dir / "artifacts")
    args = parser.parse_args()
    report = train(args.dataset, args.output_dir)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
