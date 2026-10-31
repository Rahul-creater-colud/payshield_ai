#!/usr/bin/env python
"""Profile discovered fraud-dataset CSV files without exposing raw identifiers."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import sqlite3
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SKIP_DIRECTORIES = {".git", ".ipynb_checkpoints", "__pycache__"}
MISSING_VALUES = {"", "na", "n/a", "nan", "null", "none"}
TARGET_NAMES = {"is_fraud", "fraud", "fraud_label", "label", "target"}
SAFE_SAMPLE_COLUMNS = {
    "transactions": (
        "amount",
        "timestamp",
        "transaction_type",
        "receiver_type",
        "hour_of_day",
        "is_night_transaction",
        "new_device_flag",
        "ip_location_mismatch",
        "failed_attempts_last_24h",
        "transaction_velocity",
        "amount_deviation_score",
        "is_fraud",
    ),
    "users": (
        "age_group",
        "city_tier",
        "kyc_status",
        "account_age_days",
        "linked_bank_count",
        "avg_monthly_transactions",
        "avg_transaction_value",
        "is_high_risk_user",
    ),
    "merchants": (
        "merchant_category",
        "merchant_size",
        "city_tier",
        "avg_daily_transactions",
        "is_registered",
        "rating",
    ),
    "fraud_labels": (
        "amount",
        "timestamp",
        "is_fraud",
        "new_device_flag",
        "ip_location_mismatch",
        "failed_attempts_last_24h",
        "transaction_velocity",
        "amount_deviation_score",
    ),
    "data_dictionary": ("file", "column", "dtype"),
}
INVENTORY_EXTENSIONS = {
    ".csv",
    ".ipynb",
    ".json",
    ".md",
    ".pdf",
    ".pkl",
    ".joblib",
    ".pt",
    ".pth",
    ".py",
    ".txt",
    ".parquet",
    ".xlsx",
    ".xls",
}
INSPECTED_PACKAGES = (
    "pandas",
    "numpy",
    "scikit-learn",
    "torch",
    "fastapi",
    "sqlalchemy",
    "pyarrow",
    "openpyxl",
    "joblib",
)


def _is_missing(value: str | None) -> bool:
    return value is None or value.strip().lower() in MISSING_VALUES


def _role(path: Path, columns: list[str]) -> str:
    names = set(columns)
    if {"file", "column", "description"} <= names:
        return "data_dictionary"
    if {
        "transaction_id",
        "amount",
        "is_fraud",
        "receiver_type",
        "transaction_type",
    } <= names:
        return "transactions"
    if {"transaction_id", "is_fraud"} <= names:
        return "fraud_labels"
    if "user_id" in names:
        return "users"
    if "merchant_id" in names:
        return "merchants"
    return path.stem


def _infer_type(values: list[str]) -> str:
    present = [value.strip() for value in values if not _is_missing(value)]
    if not present:
        return "empty"
    lowered = {value.lower() for value in present}
    if lowered <= {"true", "false", "yes", "no"}:
        return "boolean"
    if all(re.fullmatch(r"[+-]?\d+", value) for value in present):
        return "integer"
    try:
        for value in present:
            float(value)
        return "number"
    except ValueError:
        pass
    try:
        for value in present:
            candidate = value.replace("Z", "+00:00")
            try:
                datetime.fromisoformat(candidate)
            except ValueError:
                date.fromisoformat(candidate)
        return "datetime/date"
    except ValueError:
        return "string/category"


def _profile_csv(path: Path, project_root: Path) -> dict[str, Any]:
    try:
        stream = path.open(newline="", encoding="utf-8-sig")
    except OSError as exc:
        raise ValueError(f"Cannot open dataset {path}: {exc}") from exc

    try:
        with stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames:
                raise ValueError(f"CSV has no header: {path}")
            columns = list(reader.fieldnames)
            if len(columns) != len(set(columns)):
                raise ValueError(f"CSV contains duplicate column names: {path}")
            role = _role(path, columns)
            missing_counts = dict.fromkeys(columns, 0)
            type_samples: dict[str, list[str]] = {column: [] for column in columns}
            label_counts: dict[str, dict[str, int]] = {}
            sample_rows: list[dict[str, str]] = []
            bounds: dict[str, list[Any]] = {}
            row_count = 0
            duplicate_count = 0
            target_columns = [
                column for column in columns if column.strip().lower() in TARGET_NAMES
            ]

            with tempfile.TemporaryDirectory(prefix="payshield-dataset-profile-") as temp:
                connection = sqlite3.connect(Path(temp) / "row_hashes.sqlite")
                try:
                    connection.execute(
                        "CREATE TABLE rows (digest TEXT PRIMARY KEY) WITHOUT ROWID"
                    )
                    insert = connection.cursor()
                    for row in reader:
                        if None in row:
                            raise ValueError(
                                f"CSV row has more values than the header: {path}"
                            )
                        row_count += 1
                        for column in columns:
                            value = row.get(column, "")
                            if _is_missing(value):
                                missing_counts[column] += 1
                            elif len(type_samples[column]) < 1000:
                                type_samples[column].append(value)
                            if column.lower() == "amount":
                                try:
                                    parsed = float(value)
                                except ValueError:
                                    parsed = None
                                if parsed is not None:
                                    current = bounds.setdefault(
                                        column, [parsed, parsed]
                                    )
                                    current[0] = min(current[0], parsed)
                                    current[1] = max(current[1], parsed)
                            elif column.lower() in {"timestamp", "date"}:
                                current = bounds.setdefault(column, [value, value])
                                current[0] = min(current[0], value)
                                current[1] = max(current[1], value)

                        digest = hashlib.sha256(
                            json.dumps(
                                [row.get(column, "") for column in columns],
                                ensure_ascii=False,
                                separators=(",", ":"),
                            ).encode("utf-8")
                        ).hexdigest()
                        try:
                            insert.execute(
                                "INSERT INTO rows (digest) VALUES (?)", (digest,)
                            )
                        except sqlite3.IntegrityError:
                            duplicate_count += 1

                        for column in target_columns:
                            value = row.get(column, "").strip()
                            distribution = label_counts.setdefault(column, {})
                            distribution[value] = distribution.get(value, 0) + 1
                        if len(sample_rows) < 3:
                            sample_rows.append(row)
                    connection.commit()
                finally:
                    connection.close()
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ValueError(f"Could not read CSV {path}: {exc}") from exc

    types = {column: _infer_type(values) for column, values in type_samples.items()}
    safe_columns = SAFE_SAMPLE_COLUMNS.get(role, ())
    safe_samples = [
        {
            column: row[column]
            for column in safe_columns
            if column in row and not _is_missing(row[column])
        }
        for row in sample_rows
    ]
    return {
        "path": _relative_path(path, project_root),
        "role": role,
        "rows": row_count,
        "columns": columns,
        "types": types,
        "missing": missing_counts,
        "duplicates": duplicate_count,
        "label_distributions": label_counts,
        "bounds": bounds,
        "safe_samples": safe_samples,
    }


def _discover_csv_files(data_dir: Path) -> list[Path]:
    if not data_dir.is_dir():
        return []
    return sorted(
        path
        for path in data_dir.rglob("*.csv")
        if not any(part in SKIP_DIRECTORIES for part in path.parts)
    )


def _discover_inventory(data_dir: Path, project_root: Path) -> list[str]:
    if not data_dir.is_dir():
        return []
    files = [
        path
        for path in data_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower() in INVENTORY_EXTENSIONS
        and not any(part in SKIP_DIRECTORIES for part in path.parts)
    ]
    return [_relative_path(path, project_root) for path in sorted(files)]


def _relative_path(path: Path, project_root: Path) -> str:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return str(path)


def _markdown(value: Any) -> str:
    return str(value).replace("|", r"\|").replace("\r", " ").replace("\n", " ")


def _package_versions() -> dict[str, str]:
    versions = {}
    for package in INSPECTED_PACKAGES:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "not installed"
    return versions


def _relationship_checks(
    project_root: Path, profiles: list[dict[str, Any]]
) -> list[str]:
    by_role = {profile["role"]: project_root / profile["path"] for profile in profiles}
    if not {"transactions", "fraud_labels", "users", "merchants"} <= set(by_role):
        return []

    with tempfile.TemporaryDirectory(prefix="payshield-dataset-links-") as temp:
        connection = sqlite3.connect(Path(temp) / "links.sqlite")
        try:
            connection.executescript(
                """
                CREATE TABLE transactions (
                    transaction_id TEXT, sender_id TEXT, receiver_id TEXT,
                    receiver_type TEXT, is_fraud TEXT
                );
                CREATE TABLE labels (transaction_id TEXT, is_fraud TEXT);
                CREATE TABLE users (user_id TEXT);
                CREATE TABLE merchants (merchant_id TEXT);
                """
            )
            table_columns = {
                "transactions": (
                    "transactions",
                    ("transaction_id", "user_id", "receiver_id", "receiver_type", "is_fraud"),
                ),
                "fraud_labels": ("labels", ("transaction_id", "is_fraud")),
                "users": ("users", ("user_id",)),
                "merchants": ("merchants", ("merchant_id",)),
            }
            for role, (table, columns) in table_columns.items():
                with by_role[role].open(
                    newline="", encoding="utf-8-sig"
                ) as source:
                    reader = csv.DictReader(source)
                    placeholders = ",".join("?" for _ in columns)
                    statement = f"INSERT INTO {table} VALUES ({placeholders})"
                    batch = []
                    for row in reader:
                        batch.append(tuple(row.get(column, "") for column in columns))
                        if len(batch) == 1000:
                            connection.executemany(statement, batch)
                            batch.clear()
                    if batch:
                        connection.executemany(statement, batch)
            connection.executescript(
                """
                CREATE INDEX tx_id_idx ON transactions(transaction_id);
                CREATE INDEX label_id_idx ON labels(transaction_id);
                CREATE INDEX tx_sender_idx ON transactions(sender_id);
                CREATE INDEX tx_receiver_idx ON transactions(receiver_id);
                CREATE INDEX users_id_idx ON users(user_id);
                CREATE INDEX merchants_id_idx ON merchants(merchant_id);
                """
            )
            tx_count, tx_unique = connection.execute(
                "SELECT COUNT(*), COUNT(DISTINCT transaction_id) FROM transactions"
            ).fetchone()
            label_count, label_unique = connection.execute(
                "SELECT COUNT(*), COUNT(DISTINCT transaction_id) FROM labels"
            ).fetchone()
            different_ids = connection.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM transactions t LEFT JOIN labels l
                     ON l.transaction_id=t.transaction_id WHERE l.transaction_id IS NULL)
                  + (SELECT COUNT(*) FROM labels l LEFT JOIN transactions t
                     ON t.transaction_id=l.transaction_id WHERE t.transaction_id IS NULL)
                """
            ).fetchone()[0]
            mismatched_labels = connection.execute(
                """
                SELECT COUNT(*) FROM transactions t JOIN labels l
                  ON l.transaction_id=t.transaction_id
                 WHERE t.is_fraud != l.is_fraud
                """
            ).fetchone()[0]
            sender_missing = connection.execute(
                """
                SELECT COUNT(*) FROM transactions t LEFT JOIN users u
                  ON u.user_id=t.sender_id WHERE u.user_id IS NULL
                """
            ).fetchone()[0]
            merchant_total, merchant_missing = connection.execute(
                """
                SELECT COUNT(*), SUM(CASE WHEN m.merchant_id IS NULL THEN 1 ELSE 0 END)
                  FROM transactions t LEFT JOIN merchants m
                    ON m.merchant_id=t.receiver_id
                 WHERE LOWER(t.receiver_type)='merchant'
                """
            ).fetchone()
            user_receiver_total, user_receiver_missing = connection.execute(
                """
                SELECT COUNT(*), SUM(CASE WHEN u.user_id IS NULL THEN 1 ELSE 0 END)
                  FROM transactions t LEFT JOIN users u ON u.user_id=t.receiver_id
                 WHERE LOWER(t.receiver_type)='user'
                """
            ).fetchone()
        finally:
            connection.close()

    return [
        f"- Transaction IDs are unique: {tx_count == tx_unique}.",
        f"- Label IDs are unique: {label_count == label_unique}; transaction and label "
        f"ID sets match: {different_ids == 0}; label mismatches: {mismatched_labels:,}.",
        f"- Sender IDs resolve to users: {tx_count - sender_missing:,}/{tx_count:,}.",
        f"- Merchant receiver IDs resolve: {merchant_total - (merchant_missing or 0):,}/"
        f"{merchant_total:,}; user receiver IDs resolve: "
        f"{user_receiver_total - (user_receiver_missing or 0):,}/{user_receiver_total:,}.",
    ]


def _make_report(
    project_root: Path, data_dir: Path, profiles: list[dict[str, Any]]
) -> str:
    csv_paths = [project_root / profile["path"] for profile in profiles]
    dataset_root = Path(os.path.commonpath([str(path.parent) for path in csv_paths]))
    inventory = _discover_inventory(dataset_root, project_root)
    other_tabular = [
        item
        for item in inventory
        if Path(item).suffix.lower() in {".xlsx", ".xls", ".parquet"}
    ]
    lines = [
        "# Cloned UPI-Fraud-Detection-System dataset analysis",
        "",
        f"Dataset search location: `{_relative_path(data_dir, project_root)}`",
        "",
        f"## Repository inventory (`{_relative_path(dataset_root, project_root)}`)",
        "",
    ]
    lines.extend(f"- `{item}`" for item in inventory)
    if not inventory:
        lines.append("- No candidate dataset/document files found.")
    lines.extend(
        [
            "",
            "CSV files are profiled below. "
            + (
                "Other tabular files found but not parsed: "
                + ", ".join(f"`{item}`" for item in other_tabular)
                + "."
                if other_tabular
                else "No Excel or Parquet dataset files were found."
            ),
        ]
    )
    lines.extend(["", "## Dataset profiles", ""])
    for profile in profiles:
        lines.extend(
            [
                f"### `{profile['path']}` ({profile['role']})",
                "",
                f"- Format: CSV; rows: {profile['rows']:,}; columns: {len(profile['columns'])}",
                f"- Exact duplicate rows: {profile['duplicates']:,}",
                "",
                "| Column | Inferred type | Missing |",
                "|---|---|---:|",
            ]
        )
        for column in profile["columns"]:
            missing = profile["missing"][column]
            lines.append(
                f"| `{_markdown(column)}` | {profile['types'][column]} "
                f"| {missing:,} ({missing / profile['rows']:.2%}) |"
                if profile["rows"]
                else f"| `{_markdown(column)}` | {profile['types'][column]} | 0 |"
            )
        if profile["label_distributions"]:
            for column, distribution in profile["label_distributions"].items():
                lines.extend(
                    [
                        "",
                        f"Label distribution for `{column}`: "
                        + ", ".join(
                            f"`{_markdown(label)}` = {count:,}"
                            for label, count in sorted(distribution.items())
                        ),
                    ]
                )
        if profile["safe_samples"]:
            lines.extend(
                [
                    "",
                    "Redacted sample (identifier/name/contact fields are omitted):",
                    "",
                    "```json",
                    json.dumps(profile["safe_samples"], indent=2, ensure_ascii=False),
                    "```",
                ]
            )
        numeric = [
            column
            for column, inferred in profile["types"].items()
            if inferred in {"integer", "number", "boolean"}
        ]
        categorical = [
            column
            for column, inferred in profile["types"].items()
            if inferred in {"string/category", "datetime/date"}
        ]
        lines.extend(
            [
                "",
                f"- Numeric/boolean columns: {', '.join(f'`{c}`' for c in numeric) or 'none'}",
                f"- Categorical/date/text columns: {', '.join(f'`{c}`' for c in categorical) or 'none'}",
                "",
            ]
        )
        if profile["bounds"]:
            lines.append(
                "- Observed bounds: "
                + "; ".join(
                    f"`{column}` = {low} to {high}"
                    for column, (low, high) in profile["bounds"].items()
                )
            )
            lines.append("")

    relationship_checks = _relationship_checks(project_root, profiles)
    if relationship_checks:
        lines.extend(["## Cross-file integrity", "", *relationship_checks, ""])

    transaction = next(
        (profile for profile in profiles if profile["role"] == "transactions"), None
    )
    labels = next(
        (profile for profile in profiles if profile["role"] == "fraud_labels"), None
    )
    readme_texts = [
        path.read_text(encoding="utf-8", errors="replace").lower()
        for path in data_dir.rglob("README.md")
        if not any(part in SKIP_DIRECTORIES for part in path.parts)
    ]
    documented_synthetic = any("synthetic" in text for text in readme_texts)
    fraud_count = None
    total_count = transaction["rows"] if transaction else None
    if transaction:
        fraud_distribution = transaction["label_distributions"].get("is_fraud", {})
        fraud_count = fraud_distribution.get("1", 0)
    lines.extend(
        [
            "## Suitability and interpretation",
            "",
        ]
    )
    if transaction and "is_fraud" in transaction["columns"]:
        distribution = transaction["label_distributions"].get("is_fraud", {})
        positive = distribution.get("1", 0)
        negative = distribution.get("0", 0)
        prevalence = positive / total_count if total_count else 0
        lines.append(
            f"- The transaction table has a binary `is_fraud` target: "
            f"{positive:,} positive, {negative:,} negative "
            f"({prevalence:.2%} positive)."
        )
    elif labels:
        lines.append(
            "- A fraud label exists in a separate labels table; join labels by transaction ID "
            "only after checking one-to-one key integrity."
        )
    else:
        lines.append(
            "- No recognized fraud target was found. Supervised fraud classification is "
            "not supported until valid adjudicated labels are supplied."
        )
    if documented_synthetic:
        lines.append(
            "- The repository README documents the records as synthetically generated and "
            "describes labels derived from a hand-authored risk-signal formula. The labels "
            "are not confirmed, adjudicated real-world fraud outcomes."
        )
        lines.append(
            "- Appropriate use: preprocessing, feature engineering, pipeline smoke tests, "
            "and experiments that explicitly target agreement with the synthetic label generator. "
            "Not appropriate for claims about live UPI fraud accuracy, external validation, "
            "or operational decisions."
        )
    if transaction:
        columns = set(transaction["columns"])
        available = [
            name
            for name in (
                "amount",
                "receiver_type",
                "transaction_type",
                "user_id",
                "receiver_id",
                "timestamp",
                "hour_of_day",
                "time_since_last_txn_min",
                "transaction_velocity",
                "new_device_flag",
                "ip_location_mismatch",
                "failed_attempts_last_24h",
                "amount_deviation_score",
            )
            if name in columns
        ]
        lines.append(
            "- Present transaction, sender/receiver, and behavioral fields include: "
            + ", ".join(f"`{name}`" for name in available)
            + ". Sender/receiver IDs and linked user/merchant tables support synthetic "
            "relational and temporal experiments; IDs themselves should not be model features."
        )
        lines.append(
            "- Directly available suspicious-pattern signals include new device, IP/location "
            "mismatch, failed attempts, transaction velocity, amount deviation, night-time, "
            "KYC status, and a linked high-risk-user flag."
        )
        lines.append(
            "- `users.csv` supplies anonymized sender profile fields such as age bracket, "
            "city tier, KYC status, account age, linked-bank count, transaction averages, "
            "preferred app/device, loyalty score, and high-risk flag. `receiver_id` and "
            "`receiver_type` distinguish user/merchant receivers; merchant records include "
            "category, size, city tier, registration, and rating."
        )
        lines.append(
            "- Not present: real VPA/account numbers, phone numbers, device IDs, IP addresses, "
            "bank/provider identity, collect-request text, or confirmed payment-network events. "
            "Do not infer these from the UPI repository name."
        )
        leakage = [
            name
            for name in ("is_fraud", "status", "balance_after_transaction")
            if name in columns
        ]
        if leakage:
            lines.append(
                "- Exclude the target `is_fraud` from predictors. Treat post-transaction "
                "`status` and `balance_after_transaction` as potential outcome leakage; "
                "exclude unless their time-of-decision availability is proven."
            )
        if "user_id" in columns:
            lines.append(
                "- Transactions repeat by sender. Use a user-grouped or forward-in-time "
                "evaluation split to reduce identity/history leakage; do not randomly split "
                "rows and call the result independent-user validation."
            )
    if labels:
        lines.extend(
            [
                "- The separate fraud-labels CSV repeats target and transaction fields. Do not "
                "treat its duplicate label/signal columns as additional independent observations.",
            ]
        )
    lines.extend(
        [
            "- The existing PayShield backend has its own heuristic assessment and a separate "
            "synthetic-trained seven-feature RF package. This external schema/label source "
            "does not establish compatibility or justify replacing that model. No model "
            "training, artifact overwrite, or API-contract change is performed by this inspector.",
            "- Feature compatibility is partial: `amount`, `hour_of_day`, failed-attempts, "
            "and average-amount proxies exist. In the existing backend, failed attempts are "
            "currently assumed to be zero and are not accepted/stored by its analysis request. "
            "Its 24-hour transaction count is not equivalent to this dataset's `transaction_velocity`; "
            "receiver novelty must be derived strictly from past sender history, and its "
            "relative amount-deviation calculation must be reconciled with this dataset's "
            "normalized `amount_deviation_score` before retraining or inference integration.",
            "",
            "## Local analysis environment",
            "",
            f"- Python: {platform.python_version()}",
            "- Package versions: "
            + "; ".join(
                f"`{name}` {version}" for name, version in _package_versions().items()
            ),
            "",
            "The cloned repository contains an `app.py`, a notebook, and a PDF presentation. "
            "Its Streamlit app fits preprocessing on the full transaction table and trains "
            "a neural network during app initialization; it does not load a checked-in "
            "trained-model checkpoint. The notebook has a row-random holdout split but "
            "does not group by user, so repeated senders can cross the split.",
            "",
            "For a meaningful PayShield evaluation, obtain legally usable, de-identified "
            "transactions with adjudicated outcomes and event times; use time-forward and "
            "user-aware validation. Until then, keep results labeled synthetic and use this "
            "dataset only for controlled pipeline experiments.",
            "",
        ]
    )
    if fraud_count is not None and total_count:
        lines.append(
            f"Observed positive target count: {fraud_count:,} of {total_count:,} "
            "(the count above comes from the CSV; no model metrics are reported)."
        )
    return "\n".join(lines).rstrip() + "\n"


def inspect_dataset(
    project_root: Path, data_dir: Path, report_path: Path
) -> list[dict[str, Any]]:
    root = project_root.resolve()
    search_dir = data_dir if data_dir.is_absolute() else root / data_dir
    search_dir = search_dir.resolve()
    report_path = report_path if report_path.is_absolute() else root / report_path
    report_path = report_path.resolve()
    csv_files = _discover_csv_files(search_dir)
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV datasets found under {search_dir}. Check --data-dir or place "
            "the cloned repository under the project data directory."
        )
    profiles = [_profile_csv(path, root) for path in csv_files]
    report = _make_report(root, search_dir, profiles)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"Report written to {report_path}")
    return profiles


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=PROJECT_ROOT,
        help="Project root (defaults to the root inferred from this script).",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        help="Directory to search recursively (default: <root>/data).",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Report path (default: <root>/backend/DATASET_ANALYSIS.md).",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    data_dir = args.data_dir or root / "data"
    report_path = args.report or root / "backend" / "DATASET_ANALYSIS.md"
    try:
        inspect_dataset(root, data_dir, report_path)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Dataset inspection failed: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
