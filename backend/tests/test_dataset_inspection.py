from __future__ import annotations

from pathlib import Path

import pytest

from scripts.inspect_fraud_dataset import inspect_dataset


def test_inspector_discovers_csv_redacts_identifiers_and_counts_duplicates(tmp_path: Path):
    root = tmp_path
    dataset_dir = root / "data" / "renamed-clone"
    dataset_dir.mkdir(parents=True)
    source = dataset_dir / "records.csv"
    source.write_text(
        "transaction_id,user_id,receiver_id,amount,timestamp,receiver_type,"
        "transaction_type,is_fraud,status\n"
        "SENSITIVE_TX_ID,SENSITIVE_USER_ID,SENSITIVE_RECEIVER_ID,42.5,"
        "2024-01-01 10:00:00,User,P2P,0,Success\n"
        "SENSITIVE_TX_ID,SENSITIVE_USER_ID,SENSITIVE_RECEIVER_ID,42.5,"
        "2024-01-01 10:00:00,User,P2P,0,Success\n",
        encoding="utf-8",
    )
    before = source.read_bytes()
    report_path = root / "backend" / "DATASET_ANALYSIS.md"

    profiles = inspect_dataset(root, root / "data", report_path)

    assert len(profiles) == 1
    assert profiles[0]["role"] == "transactions"
    assert profiles[0]["rows"] == 2
    assert profiles[0]["duplicates"] == 1
    assert profiles[0]["label_distributions"] == {"is_fraud": {"0": 2}}
    report = report_path.read_text(encoding="utf-8")
    assert "SENSITIVE_TX_ID" not in report
    assert "SENSITIVE_USER_ID" not in report
    assert "SENSITIVE_RECEIVER_ID" not in report
    assert "42.5" in report
    assert source.read_bytes() == before


def test_inspector_reports_missing_dataset_directory(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="No CSV datasets found"):
        inspect_dataset(tmp_path, tmp_path / "missing", tmp_path / "report.md")
