#!/usr/bin/env python
"""Create a labeled synthetic UPI dataset and idempotently seed PayShield SQLite."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
DEFAULT_INPUT = ROOT / "ml_model" / "ml_model" / "data" / "synthetic_indian_upi_fraud_data.csv"
DEFAULT_OUTPUT = (
    ROOT / "ml_model" / "ml_model" / "data" / "enriched_indian_upi_fraud_data.csv"
)
SCENARIO_DIR = ROOT / "data" / "scenarios"

CITY_COORDINATES = (
    ("Delhi", 28.6139, 77.2090),
    ("Mumbai", 19.0760, 72.8777),
    ("Jaipur", 26.9124, 75.7873),
    ("Bengaluru", 12.9716, 77.5946),
    ("Chennai", 13.0827, 80.2707),
    ("Hyderabad", 17.3850, 78.4867),
    ("Kolkata", 22.5726, 88.3639),
    ("Pune", 18.5204, 73.8567),
    ("Ahmedabad", 23.0225, 72.5714),
    ("Lucknow", 26.8467, 80.9462),
)
BANK_HANDLES = ("okaxis", "okhdfcbank", "oksbi", "okicici", "ybl", "paytm", "airtel")
BANK_MAP = {
    "axis": "okaxis",
    "hdfc": "okhdfcbank",
    "state bank": "oksbi",
    "sbi": "oksbi",
    "icici": "okicici",
    "kotak": "kotak",
    "baroda": "bob",
}

BASE_COLUMNS = [
    "TransactionID",
    "UserID",
    "Amount",
    "Timestamp",
    "MerchantCategory",
    "TransactionType",
    "DeviceID",
    "IPAddress",
    "Latitude",
    "Longitude",
    "AvgTransactionAmount",
    "txn_per_day",
    "UnusualLocation",
    "UnusualAmount",
    "NewDevice",
    "FailedAttempts",
    "FraudFlag",
    "OriginalFraudFlag",
    "PhoneNumber",
    "PhoneNumberLabel",
    "BankName",
    "City",
    "sender_id",
    "sender_vpa",
    "receiver_id",
    "receiver_vpa",
    "request_type",
    "session_id",
    "IsNewRecipient",
    "FraudPattern",
    "data_label",
]


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--fraud-rate",
        type=float,
        default=0.025,
        help="Target overall FraudFlag prevalence (default: 0.025, about 2.5%%).",
    )
    parser.add_argument("--seed", type=int, default=20261031)
    parser.add_argument(
        "--database-url",
        help="Override DB_URL for this run; defaults to backend/app.config settings.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete only this script's reserved CSV_/DEMO_ seed records before reseeding.",
    )
    args = parser.parse_args()
    if not 0.005 <= args.fraud_rate <= 0.30:
        parser.error("--fraud-rate must be between 0.005 and 0.30.")
    if args.database_url:
        os.environ["DB_URL"] = args.database_url
    return args


def _absolute(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _phone_number(index: int) -> str:
    return f"{6 + index % 4}{index // 4:09d}"


def _handle_for_bank(bank_name: str, index: int) -> str:
    lowered = bank_name.lower()
    for key, handle in BANK_MAP.items():
        if key in lowered:
            return handle
    return BANK_HANDLES[index % len(BANK_HANDLES)]


def _to_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _format_bool(value: bool) -> str:
    return "True" if value else "False"


def _txn_per_day(value: str) -> int:
    match = re.fullmatch(r"\s*(\d+)\s*(?:/\s*day)?\s*", value, re.IGNORECASE)
    if not match:
        raise ValueError(f"Invalid TransactionFrequency value: {value!r}")
    return int(match.group(1))


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def _row_city(row_index: int, transaction_id: str) -> tuple[str, float, float]:
    value = int(_digest(transaction_id)[:16], 16)
    city, latitude, longitude = CITY_COORDINATES[(value + row_index) % len(CITY_COORDINATES)]
    latitude_jitter = (((value >> 8) % 4001) / 100000) - 0.02
    longitude_jitter = (((value >> 24) % 4001) / 100000) - 0.02
    return city, round(latitude + latitude_jitter, 6), round(longitude + longitude_jitter, 6)


def _scenario_data() -> dict[str, dict[str, Any]]:
    scenarios: dict[str, dict[str, Any]] = {}
    for path in sorted(SCENARIO_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as file:
            scenario = json.load(file)
        scenario_id = scenario.get("scenario_id")
        if scenario_id not in {"A", "B", "C", "D"} or scenario_id in scenarios:
            raise ValueError(f"Unexpected or duplicate scenario in {path}")
        if scenario.get("data_label") != "DEMO DATA" or scenario.get("simulated") is not True:
            raise ValueError(f"{path.name} must explicitly identify synthetic demo data.")
        scenarios[scenario_id] = scenario
    if set(scenarios) != {"A", "B", "C", "D"}:
        raise ValueError("Expected exactly scenarios A, B, C, and D in data/scenarios/.")
    return scenarios


def _read_source(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file():
        raise FileNotFoundError(f"Source CSV was not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {path}")
        missing = set(
            (
                "TransactionID",
                "UserID",
                "Amount",
                "Timestamp",
                "TransactionType",
                "TransactionFrequency",
                "FraudFlag",
                "PhoneNumber",
                "BankName",
            )
        ) - set(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")
        return list(reader.fieldnames), list(reader)


def _normalize_rows(
    source_rows: list[dict[str, str]], seed: int, fraud_rate: float
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    profiles: dict[str, dict[str, Any]] = {}
    familiar_recipients = [f"CSV_FAM_{index:03d}" for index in range(1, 41)]

    for index, source in enumerate(source_rows):
        source_id = source["TransactionID"].strip()
        user_hash = _digest(source["UserID"].strip())
        transaction_hash = _digest(source_id)
        sender_id = f"CSVU_{user_hash[:24]}"
        phone_number = _phone_number(index)
        bank_name = source["BankName"].strip() or "Synthetic Bank"
        bank_handle = _handle_for_bank(bank_name, index)
        sender_vpa = f"user{user_hash[:12]}@{bank_handle}"
        is_new_recipient = int(transaction_hash[:8], 16) % 10 == 0

        if is_new_recipient:
            receiver_id = f"CSV_NEW_{source_id}"
            receiver_vpa = f"newpayee{source_id}@{BANK_HANDLES[int(transaction_hash[8:12], 16) % len(BANK_HANDLES)]}"
        else:
            familiar_index = int(transaction_hash[8:16], 16) % len(familiar_recipients)
            receiver_id = familiar_recipients[familiar_index]
            receiver_vpa = (
                f"recipient{familiar_index + 1:03d}@"
                f"{BANK_HANDLES[familiar_index % len(BANK_HANDLES)]}"
            )

        city, latitude, longitude = _row_city(index, source_id)
        amount = float(source["Amount"])
        transaction_type = source["TransactionType"].strip().upper()
        if transaction_type not in {"P2P", "P2M"}:
            raise ValueError(
                f"Unsupported TransactionType {transaction_type!r} in transaction {source_id}"
            )
        timestamp = _timestamp(source["Timestamp"])
        original_flag = _to_bool(source["FraudFlag"])
        usual_recipients = [
            familiar_recipients[
                (int(user_hash[:8], 16) + offset) % len(familiar_recipients)
            ]
            for offset in range(5)
        ]
        profile = {
            "avg_amount": round(float(source["AvgTransactionAmount"]), 2),
            "typical_hours": [8, 22],
            "txn_per_day": _txn_per_day(source["TransactionFrequency"]),
            "usual_recipients": usual_recipients,
            "max_amount": round(max(amount, float(source["AvgTransactionAmount"]) * 3), 2),
            "txn_per_week": _txn_per_day(source["TransactionFrequency"]) * 7,
            "usual_hours": [8, 22],
            "known_recipients": usual_recipients,
            "data_label": "DEMO DATA",
        }
        profiles[sender_id] = {
            "user_id": sender_id,
            "display_name": f"Synthetic User {index + 1:05d}",
            "baseline_profile": profile,
        }

        rows.append(
            {
                **source,
                "TransactionID": f"CSV_TX_{source_id}",
                "UserID": sender_id,
                "Amount": f"{amount:.2f}",
                "Timestamp": timestamp.isoformat(),
                "TransactionType": transaction_type,
                "Latitude": f"{latitude:.6f}",
                "Longitude": f"{longitude:.6f}",
                "txn_per_day": _txn_per_day(source["TransactionFrequency"]),
                "UnusualLocation": _format_bool(_to_bool(source.get("UnusualLocation", ""))),
                "UnusualAmount": _format_bool(_to_bool(source.get("UnusualAmount", ""))),
                "NewDevice": _format_bool(_to_bool(source.get("NewDevice", ""))),
                "FailedAttempts": int(source.get("FailedAttempts") or 0),
                "FraudFlag": False,
                "OriginalFraudFlag": _format_bool(original_flag),
                "PhoneNumber": phone_number,
                "PhoneNumberLabel": "SYNTHETIC",
                "BankName": bank_name,
                "City": city,
                "sender_id": sender_id,
                "sender_vpa": sender_vpa,
                "receiver_id": receiver_id,
                "receiver_vpa": receiver_vpa,
                "request_type": "PAY",
                "session_id": "",
                "IsNewRecipient": _format_bool(is_new_recipient),
                "FraudPattern": "GENUINE_NEW_RECIPIENT" if is_new_recipient else "NONE",
                "data_label": "DEMO DATA",
                "_source_fraud": original_flag,
                "_source_index": index,
            }
        )

    # Reserve labels for the explicit A/B scam scenarios and the genuine D case.
    scenario_fraud_count = 1 + 12 + 3
    total_rows = len(rows) + scenario_fraud_count + 1
    target_fraud_count = int(math.floor(total_rows * fraud_rate + 0.5))
    base_target = target_fraud_count - scenario_fraud_count
    if base_target < 20:
        raise ValueError(
            "The requested fraud rate is too low to retain the 20 explicit night-risk "
            "examples plus scenario A/B labels."
        )
    if base_target > len(rows):
        raise ValueError("Target fraud count exceeds the number of source transactions.")

    source_positive = [index for index, row in enumerate(rows) if row["_source_fraud"]]
    source_negative = [index for index, row in enumerate(rows) if not row["_source_fraud"]]
    if base_target <= len(source_positive):
        selected = set(rng.sample(source_positive, base_target))
    else:
        selected = set(source_positive)
        selected.update(rng.sample(source_negative, base_target - len(selected)))
    for index, row in enumerate(rows):
        is_fraud = index in selected
        row["FraudFlag"] = _format_bool(is_fraud)
        row["FraudPattern"] = (
            "SYNTHETIC_REBALANCED_FRAUD"
            if is_fraud
            else "GENUINE_NEW_RECIPIENT" if row["IsNewRecipient"] == "True" else "NONE"
        )

    night_indices = rng.sample(sorted(selected), 20)
    for index in night_indices:
        row = rows[index]
        original_time = _timestamp(str(row["Timestamp"]))
        night_time = original_time.replace(hour=2 + (index % 3), minute=index % 60)
        row["Timestamp"] = night_time.isoformat()
        row["Amount"] = f"{max(float(row['Amount']), 25000.0 + (index % 5000)):.2f}"
        row["AvgTransactionAmount"] = f"{float(row['AvgTransactionAmount']):.2f}"
        row["UnusualAmount"] = "True"
        row["NewDevice"] = "True"
        row["FailedAttempts"] = max(int(row["FailedAttempts"]), 3)
        row["FraudPattern"] = "NIGHT_HIGH_AMOUNT_NEW_DEVICE_FAILED_ATTEMPTS"

    for row in rows:
        row.pop("_source_fraud")
        row.pop("_source_index")
    return rows, list(profiles.values())


def _scenario_row(
    *,
    transaction_id: str,
    sender_id: str,
    sender_vpa: str,
    receiver_id: str,
    receiver_vpa: str,
    amount: float,
    timestamp: str,
    transaction_type: str,
    request_type: str,
    fraud_flag: bool,
    fraud_pattern: str,
    phone_number: str,
    is_new_recipient: bool = False,
) -> dict[str, Any]:
    return {
        "TransactionID": transaction_id,
        "UserID": sender_id,
        "Amount": f"{amount:.2f}",
        "Timestamp": timestamp,
        "MerchantCategory": "Synthetic Demo",
        "TransactionType": transaction_type,
        "DeviceID": "DEMO_DEVICE",
        "IPAddress": "192.0.2.10",
        "Latitude": "28.613900",
        "Longitude": "77.209000",
        "AvgTransactionAmount": f"{amount:.2f}",
        "txn_per_day": 1,
        "UnusualLocation": "False",
        "UnusualAmount": _format_bool(amount >= 20000),
        "NewDevice": "False",
        "FailedAttempts": 0,
        "FraudFlag": _format_bool(fraud_flag),
        "OriginalFraudFlag": "False",
        "PhoneNumber": phone_number,
        "PhoneNumberLabel": "SYNTHETIC",
        "BankName": "Synthetic Demo Bank",
        "City": "Delhi",
        "sender_id": sender_id,
        "sender_vpa": sender_vpa,
        "receiver_id": receiver_id,
        "receiver_vpa": receiver_vpa,
        "request_type": request_type,
        "session_id": "",
        "IsNewRecipient": _format_bool(is_new_recipient),
        "FraudPattern": fraud_pattern,
        "data_label": "DEMO DATA",
    }


def _append_scenarios(
    rows: list[dict[str, Any]], scenarios: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    scenario_users: list[dict[str, Any]] = []
    scenario_accounts: list[dict[str, Any]] = []
    scenario_a = scenarios["A"]
    scenario_b = scenarios["B"]
    scenario_d = scenarios["D"]

    def add_demo_user(user_id: str, display_name: str, recipients: list[str]) -> None:
        scenario_users.append(
            {
                "user_id": user_id,
                "display_name": display_name,
                "baseline_profile": {
                    "avg_amount": 1200.0,
                    "typical_hours": [8, 22],
                    "txn_per_day": 2,
                    "usual_recipients": recipients,
                    "max_amount": 5000.0,
                    "txn_per_week": 14,
                    "usual_hours": [8, 22],
                    "known_recipients": recipients,
                    "data_label": "DEMO DATA",
                },
            }
        )

    def add_demo_account(
        account_id: str, vpa: str, phone_index: int, report_status: str = "NONE"
    ) -> None:
        scenario_accounts.append(
            {
                "account_id": account_id,
                "vpa": vpa,
                "mobile": _phone_number(phone_index),
                "created_at_if_known": None,
                "report_status": report_status,
                "risk_context": {
                    "data_label": "DEMO DATA",
                    "mobile_data_label": "SYNTHETIC",
                    "simulated": True,
                },
            }
        )

    a_receiver = scenario_a["receiver_id"]
    add_demo_account(a_receiver, scenario_a["receiver_vpa"], 11000, "REPORTED")
    pending_merchant = scenarios["C"]["merchant_id"]
    add_demo_account(pending_merchant, "merchant.pending.demo@okaxis", 11001)
    a_row = _scenario_row(
        transaction_id=scenario_a["transaction_id"],
        sender_id=scenario_a["sender_id"],
        sender_vpa="aarav.demo@okaxis",
        receiver_id=a_receiver,
        receiver_vpa=scenario_a["receiver_vpa"],
        amount=float(scenario_a["amount"]),
        timestamp=scenario_a["timestamp"],
        transaction_type=scenario_a["transaction_type"],
        request_type=scenario_a["request_type"],
        fraud_flag=True,
        fraud_pattern=scenario_a["fraud_pattern"],
        phone_number=_phone_number(11001),
    )
    rows.append(a_row)

    hub = scenario_b["hub_id"]
    add_demo_user(hub, "Synthetic Mule Hub", [])
    add_demo_account(hub, "mule.hub.demo@ybl", 11002, "REPORTED")
    hop_chain = scenario_b["hop_chain"]
    for index, account_id in enumerate(hop_chain[1:], start=1):
        add_demo_account(
            account_id,
            f"mule.hop{index}.demo@{BANK_HANDLES[index % len(BANK_HANDLES)]}",
            11002 + index,
            "REPORTED" if index == len(hop_chain) - 1 else "NONE",
        )
        add_demo_user(account_id, f"Synthetic Mule Hop {index}", [])

    for feeder_index in range(1, int(scenario_b["feeder_count"]) + 1):
        sender_id = f"DEMO_MULE_FEEDER_{feeder_index:02d}"
        sender_vpa = f"feeder{feeder_index:02d}.demo@{BANK_HANDLES[feeder_index % len(BANK_HANDLES)]}"
        add_demo_user(sender_id, f"Synthetic Feeder {feeder_index:02d}", [hub])
        add_demo_account(sender_id, sender_vpa, 11100 + feeder_index)
        rows.append(
            _scenario_row(
                transaction_id=f"{scenario_b['feeder_transaction_prefix']}{feeder_index:02d}",
                sender_id=sender_id,
                sender_vpa=sender_vpa,
                receiver_id=hub,
                receiver_vpa="mule.hub.demo@ybl",
                amount=2200.0 + feeder_index * 100,
                timestamp=(
                    datetime.fromisoformat(scenario_a["timestamp"])
                    + timedelta(minutes=feeder_index)
                ).isoformat(),
                transaction_type="P2P",
                request_type=scenario_b["request_type"],
                fraud_flag=True,
                fraud_pattern=scenario_b["fraud_pattern_fan_in"],
                phone_number=_phone_number(11200 + feeder_index),
            )
        )

    for hop_index, (sender_id, receiver_id) in enumerate(
        zip(hop_chain, hop_chain[1:]), start=1
    ):
        receiver_account = next(
            account for account in scenario_accounts if account["account_id"] == receiver_id
        )
        rows.append(
            _scenario_row(
                transaction_id=f"{scenario_b['onward_transaction_prefix']}{hop_index:02d}",
                sender_id=sender_id,
                sender_vpa=next(
                    account["vpa"]
                    for account in scenario_accounts
                    if account["account_id"] == sender_id
                ),
                receiver_id=receiver_id,
                receiver_vpa=receiver_account["vpa"],
                amount=1500.0 + hop_index * 100,
                timestamp=(
                    datetime.fromisoformat(scenario_a["timestamp"])
                    + timedelta(minutes=13 + hop_index)
                ).isoformat(),
                transaction_type="P2P",
                request_type=scenario_b["request_type"],
                fraud_flag=True,
                fraud_pattern=f"{scenario_b['fraud_pattern_onward_prefix']}{hop_index}",
                phone_number=_phone_number(11300 + hop_index),
            )
        )

    d_row = _scenario_row(
        transaction_id=scenario_d["transaction_id"],
        sender_id=scenario_d["sender_id"],
        sender_vpa="aarav.demo@okaxis",
        receiver_id=scenario_d["receiver_id"],
        receiver_vpa=scenario_d["receiver_vpa"],
        amount=float(scenario_d["amount"]),
        timestamp=scenario_d["timestamp"],
        transaction_type=scenario_d["transaction_type"],
        request_type=scenario_d["request_type"],
        fraud_flag=False,
        fraud_pattern=scenario_d["fraud_pattern"],
        phone_number=_phone_number(11400),
        is_new_recipient=True,
    )
    rows.append(d_row)

    return rows, {"users": scenario_users, "accounts": scenario_accounts}


def _assign_merchant_sessions(
    rows: list[dict[str, Any]], scenarios: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    eligible = [
        row
        for row in rows
        if row["TransactionType"] == "P2M"
        and row["TransactionID"].startswith("CSV_TX_")
        and row["IsNewRecipient"] == "False"
    ]
    if len(eligible) < 29:
        raise ValueError("At least 29 familiar P2M rows are required for demo merchant sessions.")

    sessions: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    for index, row in enumerate(eligible[:29], start=1):
        session_id = f"DEMO_SESSION_CSV_{index:03d}"
        row["session_id"] = session_id
        timestamp = _timestamp(str(row["Timestamp"]))
        status = "FAILED" if index % 5 == 0 else "SUCCESS"
        sessions.append(
            {
                "session_id": session_id,
                "merchant_id": row["receiver_id"],
                "expected_amount": float(row["Amount"]),
                "created_at": timestamp.isoformat(),
                "status": status,
            }
        )
        events.append(
            {
                "event_id": f"DEMO_EVENT_{index:03d}",
                "session_id": session_id,
                "provider_reference": f"DEMO-SIM-REF-{index:03d}",
                "status": status,
                "simulated": True,
                "verified_at": (timestamp + timedelta(minutes=1)).isoformat(),
            }
        )

    pending = scenarios["C"]
    sessions.append(
        {
            "session_id": pending["session_id"],
            "merchant_id": pending["merchant_id"],
            "expected_amount": float(pending["expected_amount"]),
            "created_at": pending["created_at"] if "created_at" in pending else scenarios["A"]["timestamp"],
            "status": "PENDING",
        }
    )
    return sessions, events, eligible[:29]


def _profiles_for_seed(
    csv_profiles: list[dict[str, Any]], scenario_users: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    profiles = {row["user_id"]: row for row in csv_profiles}
    profiles.update({row["user_id"]: row for row in scenario_users})
    for user_id in ("U001",):
        if user_id not in profiles:
            profiles[user_id] = {
                "user_id": user_id,
                "display_name": "Aarav Sharma",
                "baseline_profile": {
                    "avg_amount": 1200.0,
                    "typical_hours": [8, 22],
                    "txn_per_day": 2,
                    "usual_recipients": ["ACC_101", "ACC_102", "ACC_103"],
                    "max_amount": 5000.0,
                    "txn_per_week": 14,
                    "usual_hours": [8, 22],
                    "known_recipients": ["ACC_101", "ACC_102", "ACC_103"],
                    "data_label": "DEMO DATA",
                },
            }
    return list(profiles.values())


def _intelligence_rows() -> list[dict[str, Any]]:
    now = datetime.fromisoformat("2026-10-31T04:00:00+00:00").isoformat()
    rows: list[dict[str, Any]] = []
    for index in range(1, 41):
        rows.append(
            {
                "indicator_id": f"DEMO_INTEL_VPA_{index:03d}",
                "indicator_type": "VPA",
                "indicator_value": f"indicator{index:03d}.demo@{BANK_HANDLES[index % len(BANK_HANDLES)]}",
                "source": "DEMO DATA — synthetic indicator fixture",
                "confidence": round(0.55 + (index % 40) / 100, 2),
                "review_status": "UNREVIEWED",
                "reported_at": now,
                "reviewed_at": None,
            }
        )
    for index in range(1, 21):
        rows.append(
            {
                "indicator_id": f"DEMO_INTEL_PHONE_{index:03d}",
                "indicator_type": "MOBILE",
                "indicator_value": _phone_number(20000 + index),
                "source": "DEMO DATA — synthetic indicator fixture; phone is synthetic",
                "confidence": round(0.55 + (index % 40) / 100, 2),
                "review_status": "UNREVIEWED",
                "reported_at": now,
                "reviewed_at": None,
            }
        )
    for index in range(1, 21):
        rows.append(
            {
                "indicator_id": f"DEMO_INTEL_URL_{index:03d}",
                "indicator_type": "URL",
                "indicator_value": f"https://demo-indicator-{index:03d}.invalid/review",
                "source": "DEMO DATA — synthetic indicator fixture",
                "confidence": round(0.55 + (index % 40) / 100, 2),
                "review_status": "UNREVIEWED",
                "reported_at": now,
                "reviewed_at": None,
            }
        )
    for index in range(1, 21):
        rows.append(
            {
                "indicator_id": f"DEMO_INTEL_DOMAIN_{index:03d}",
                "indicator_type": "DOMAIN",
                "indicator_value": f"demo-domain-{index:03d}.invalid",
                "source": "DEMO DATA — synthetic indicator fixture",
                "confidence": round(0.55 + (index % 40) / 100, 2),
                "review_status": "UNREVIEWED",
                "reported_at": now,
                "reviewed_at": None,
            }
        )
    return rows


def _scenario_assessments(
    rows: list[dict[str, Any]], scenarios: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    by_id = {row["TransactionID"]: row for row in rows}
    assessment_specs = [
        (
            scenarios["A"]["transaction_id"],
            "DEMO_SCENARIO_A_ASSESSMENT",
            int(scenarios["A"]["risk_score"]),
            "HIGH",
            "STOP_AND_REVIEW",
            "Synthetic unsolicited refund collect request; approving may debit the payer.",
        ),
        (
            f"{scenarios['B']['feeder_transaction_prefix']}01",
            "DEMO_SCENARIO_B_ASSESSMENT",
            int(scenarios["B"]["risk_score"]),
            "HIGH",
            "STOP_AND_REVIEW",
            "Synthetic fan-in and rapid onward-transfer graph pattern for review.",
        ),
        (
            scenarios["D"]["transaction_id"],
            scenarios["D"]["grievance_assessment_id"],
            int(scenarios["D"]["risk_score"]),
            "MEDIUM",
            "CAUTION_VERIFY",
            "New recipient warrants verification only; this genuine demo transaction is not labeled fraud.",
        ),
    ]
    result = []
    for transaction_id, assessment_id, score, category, action, reason in assessment_specs:
        transaction = by_id.get(transaction_id)
        if transaction is None:
            raise ValueError(f"Missing scenario transaction for assessment: {transaction_id}")
        result.append(
            {
                "assessment_id": assessment_id,
                "transaction_id": transaction_id,
                "score": score,
                "category": category,
                "reasons": [
                    {
                        "code": "DEMO_SCENARIO",
                        "layer": "synthetic_scenario",
                        "text": reason,
                        "weight": score,
                    }
                ],
                "recommended_action": action,
                "playbook_matches": [],
                "model_version": "synthetic-seed-v1",
                "created_at": transaction["Timestamp"],
            }
        )
    return result


def _scenario_grievance(scenario: dict[str, Any]) -> dict[str, Any]:
    created = scenario["timestamp"]
    return {
        "case_id": scenario["grievance_case_id"],
        "user_reference": scenario["sender_id"],
        "assessment_id": scenario["grievance_assessment_id"],
        "reason": scenario["grievance_reason"],
        "evidence_ref": "DEMO DATA — scenario D synthetic record",
        "status": "SUBMITTED",
        "reviewer_note": None,
        "status_history": [{"status": "SUBMITTED", "note": None, "at": created}],
        "created_at": created,
        "updated_at": created,
    }


def _account_rows(
    rows: list[dict[str, Any]],
    csv_profiles: list[dict[str, Any]],
    scenario_accounts: list[dict[str, Any]],
    p2m_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    accounts: dict[str, dict[str, Any]] = {}
    profile_lookup = {row["user_id"]: row for row in csv_profiles}
    for row in rows:
        if row["TransactionID"].startswith("CSV_TX_"):
            user_id = row["sender_id"]
            user_profile = profile_lookup[user_id]["baseline_profile"]
            accounts[user_id] = {
                "account_id": user_id,
                "vpa": row["sender_vpa"],
                "mobile": row["PhoneNumber"],
                "created_at_if_known": None,
                "report_status": "NONE",
                "risk_context": {
                    "data_label": "DEMO DATA",
                    "mobile_data_label": "SYNTHETIC",
                    "txn_per_day": user_profile["txn_per_day"],
                },
            }

    familiar_ids = {row["receiver_id"] for row in rows if row["receiver_id"].startswith("CSV_FAM_")}
    for account_id in familiar_ids:
        index = int(account_id.rsplit("_", 1)[1])
        accounts[account_id] = {
            "account_id": account_id,
            "vpa": f"recipient{index:03d}@{BANK_HANDLES[index % len(BANK_HANDLES)]}",
            "mobile": _phone_number(12000 + index),
            "created_at_if_known": None,
            "report_status": "NONE",
            "risk_context": {"data_label": "DEMO DATA", "mobile_data_label": "SYNTHETIC"},
        }
    for row in scenario_accounts:
        accounts[row["account_id"]] = row
    for row in p2m_rows:
        # Merchant sessions reference only familiar local demo accounts.
        receiver_id = row["receiver_id"]
        if receiver_id.startswith("CSV_FAM_") and receiver_id not in accounts:
            index = int(receiver_id.rsplit("_", 1)[1])
            accounts[receiver_id] = {
                "account_id": receiver_id,
                "vpa": row["receiver_vpa"],
                "mobile": _phone_number(12000 + index),
                "created_at_if_known": None,
                "report_status": "NONE",
                "risk_context": {"data_label": "DEMO DATA", "mobile_data_label": "SYNTHETIC"},
            }
    return list(accounts.values())


def _write_enriched_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=BASE_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _remove_script_seed(db: Any, model_map: dict[str, Any]) -> None:
    from sqlalchemy import delete
    from app.models import (
        Grievance,
        GraphEdge,
        PaymentEvent,
        RiskAssessment,
        RiskAssessmentResolution,
        Transaction,
    )

    scenario_grievance = "DEMO_SCENARIO_D_GRIEVANCE"
    db.execute(delete(Grievance).where(Grievance.case_id == scenario_grievance))

    assessments = db.query(RiskAssessment).all()
    owned_assessment_ids = [
        item.assessment_id
        for item in assessments
        if item.assessment_id.startswith("DEMO_SCENARIO_")
        or item.assessment_id.startswith("CSV_ASM_")
    ]
    transaction_ids = [
        item.transaction_id
        for item in db.query(Transaction).all()
        if item.transaction_id.startswith("CSV_TX_")
        or item.transaction_id.startswith("DEMO_SCENARIO_")
    ]
    owned_assessment_ids.extend(
        item.assessment_id for item in assessments if item.transaction_id in transaction_ids
    )
    if owned_assessment_ids:
        db.execute(
            delete(RiskAssessmentResolution).where(
                RiskAssessmentResolution.assessment_id.in_(set(owned_assessment_ids))
            )
        )
        db.execute(
            delete(RiskAssessment).where(
                RiskAssessment.assessment_id.in_(set(owned_assessment_ids))
            )
        )

    if transaction_ids:
        db.execute(delete(GraphEdge).where(GraphEdge.transaction_id.in_(transaction_ids)))
        db.execute(delete(Transaction).where(Transaction.transaction_id.in_(transaction_ids)))

    for model, primary_key, prefixes in (
        (PaymentEvent, "event_id", ("DEMO_EVENT_",)),
        (model_map["merchant_sessions"], "session_id", ("DEMO_SESSION_",)),
        (model_map["fraud_intelligence"], "indicator_id", ("DEMO_INTEL_",)),
        (model_map["accounts_or_vpas"], "account_id", ("CSVU_", "CSV_FAM_", "DEMO_")),
        (model_map["demo_users"], "user_id", ("CSVU_", "DEMO_MULE_")),
    ):
        objects = db.query(model).all()
        keys = [
            getattr(obj, primary_key)
            for obj in objects
            if any(str(getattr(obj, primary_key)).startswith(prefix) for prefix in prefixes)
        ]
        if keys:
            db.execute(delete(model).where(getattr(model, primary_key).in_(keys)))
    db.commit()


def _upsert_mappings(db: Any, model: Any, primary_key: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    key_column = getattr(model, primary_key)
    for offset in range(0, len(rows), 400):
        batch = rows[offset : offset + 400]
        keys = [row[primary_key] for row in batch]
        existing = {
            getattr(item, primary_key): item
            for item in db.query(model).filter(key_column.in_(keys)).all()
        }
        inserts: list[dict[str, Any]] = []
        updates: list[dict[str, Any]] = []
        for row in batch:
            if row[primary_key] in existing:
                updates.append(row)
            else:
                inserts.append(row)
        if inserts:
            db.bulk_insert_mappings(model, inserts)
        if updates:
            db.bulk_update_mappings(model, updates)
    db.flush()


def _seed_database(
    *,
    scenarios: dict[str, dict[str, Any]],
    rows: list[dict[str, Any]],
    csv_profiles: list[dict[str, Any]],
    scenario_data: dict[str, Any],
    sessions: list[dict[str, Any]],
    events: list[dict[str, Any]],
    assessments: list[dict[str, Any]],
    grievance: dict[str, Any],
    intel_rows: list[dict[str, Any]],
    account_rows: list[dict[str, Any]],
    reset: bool,
) -> None:
    os.chdir(BACKEND_ROOT)
    sys.path.insert(0, str(BACKEND_ROOT))
    from sqlalchemy import delete
    from app import models
    from app.config import settings
    from app.database import Base, SessionLocal, engine

    Base.metadata.create_all(bind=engine)
    print(f"Seeding SQLAlchemy database: {engine.url}")
    if reset:
        reset_db = SessionLocal()
        try:
            _remove_script_seed(
                reset_db,
                {
                "merchant_sessions": models.MerchantSession,
                "fraud_intelligence": models.FraudIntelligence,
                "accounts_or_vpas": models.AccountOrVPA,
                "demo_users": models.DemoUser,
                },
            )
        finally:
            reset_db.close()

    source_transactions: list[dict[str, Any]] = []
    graph_edges: list[dict[str, Any]] = []
    for row in rows:
        transaction = {
            "transaction_id": row["TransactionID"],
            "sender_id": row["sender_id"],
            "receiver_id": row["receiver_id"],
            "amount": float(row["Amount"]),
            "timestamp": row["Timestamp"],
            "status": "FLAGGED" if _to_bool(row["FraudFlag"]) else "COMPLETED",
            "request_type": row["request_type"],
            "session_id": row["session_id"] or None,
        }
        source_transactions.append(transaction)
        graph_edges.append(
            {
                "source_account": row["sender_id"],
                "target_account": row["receiver_id"],
                "amount": float(row["Amount"]),
                "timestamp": row["Timestamp"],
                "transaction_id": row["TransactionID"],
            }
        )

    for scenario_id, assessment in zip(("A", "B", "D"), assessments):
        scenario = scenarios[scenario_id]
        if scenario_id == "A":
            sender_vpa = "aarav.demo@okaxis"
            receiver_vpa = scenario["receiver_vpa"]
            receiver_id = scenario["receiver_id"]
        elif scenario_id == "B":
            sender_vpa = "feeder01.demo@ybl"
            receiver_vpa = scenario["hub_id"]
            receiver_id = scenario["hub_id"]
        else:
            sender_vpa = "aarav.demo@okaxis"
            receiver_vpa = scenario["receiver_vpa"]
            receiver_id = scenario["receiver_id"]
        transaction = next(
            item for item in source_transactions if item["transaction_id"] == assessment["transaction_id"]
        )
        transaction["sender_id"] = scenario["sender_id"] if scenario_id != "B" else "DEMO_MULE_FEEDER_01"
        transaction["receiver_id"] = receiver_id
        graph_edges = [edge for edge in graph_edges if edge["transaction_id"] != transaction["transaction_id"]]
        graph_edges.append(
            {
                "source_account": transaction["sender_id"],
                "target_account": receiver_id,
                "amount": transaction["amount"],
                "timestamp": transaction["timestamp"],
                "transaction_id": transaction["transaction_id"],
            }
        )
        request_type = scenario.get("request_type", "PAY")
        transaction["request_type"] = (
            "COLLECT_REQUEST" if request_type == "COLLECT" else request_type
        )
        transaction["status"] = "FLAGGED" if assessment["category"] in {"MEDIUM", "HIGH"} else "COMPLETED"

    # CSV and scenario records use reserved IDs so repeat runs update, rather than duplicate, them.
    db = SessionLocal()
    try:
        _upsert_mappings(
            db,
            models.DemoUser,
            "user_id",
            _profiles_for_seed(csv_profiles, scenario_data["users"]),
        )
        # Existing seeded U001 is used by scenarios A and D; enrich its profile without replacing
        # unrelated baseline fields or changing any other established demo account.
        aarav = db.get(models.DemoUser, "U001")
        if aarav is not None:
            profile = dict(aarav.baseline_profile or {})
            usual = profile.get("known_recipients", ["ACC_101", "ACC_102", "ACC_103"])
            profile.update(
                {
                    "avg_amount": float(profile.get("avg_amount", 1200.0)),
                    "typical_hours": profile.get("typical_hours", profile.get("usual_hours", [8, 22])),
                    "txn_per_day": int(profile.get("txn_per_day", 2)),
                    "usual_recipients": profile.get("usual_recipients", usual),
                    "data_label": "DEMO DATA",
                }
            )
            aarav.baseline_profile = profile
        _upsert_mappings(db, models.AccountOrVPA, "account_id", account_rows)
        _upsert_mappings(db, models.Transaction, "transaction_id", source_transactions)
        _upsert_mappings(db, models.FraudIntelligence, "indicator_id", intel_rows)
        _upsert_mappings(db, models.MerchantSession, "session_id", sessions)
        _upsert_mappings(db, models.PaymentEvent, "event_id", events)
        _upsert_mappings(db, models.RiskAssessment, "assessment_id", assessments)
        _upsert_mappings(db, models.Grievance, "case_id", [grievance])

        # graph_edges has an auto-increment primary key; replace only edges tied to this seed namespace.
        seeded_transaction_ids = [item["transaction_id"] for item in source_transactions]
        if seeded_transaction_ids:
            for offset in range(0, len(seeded_transaction_ids), 400):
                db.execute(
                    delete(models.GraphEdge).where(
                        models.GraphEdge.transaction_id.in_(
                            seeded_transaction_ids[offset : offset + 400]
                        )
                    )
                )
        db.bulk_insert_mappings(models.GraphEdge, graph_edges)
        db.commit()
        print(
            "Seeded rows: "
            f"transactions={len(source_transactions)}, users={len(csv_profiles) + len(scenario_data['users'])}, "
            f"accounts={len(account_rows)}, graph_edges={len(graph_edges)}, "
            f"intelligence={len(intel_rows)}, sessions={len(sessions)}, "
            f"payment_events={len(events)}, assessments={len(assessments)}, grievances=1"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print(f"DB_URL setting: {settings.DB_URL}")


def main() -> None:
    args = _arguments()
    input_path = _absolute(args.input_csv)
    output_path = _absolute(args.output_csv)
    scenarios = _scenario_data()
    _headers, source_rows = _read_source(input_path)
    rows, csv_profiles = _normalize_rows(source_rows, args.seed, args.fraud_rate)
    rows, scenario_data = _append_scenarios(rows, scenarios)

    # Only a small, explicit sample of merchant payments has ledger sessions.
    sessions, events, p2m_rows = _assign_merchant_sessions(rows, scenarios)
    assessments = _scenario_assessments(rows, scenarios)
    accounts = _account_rows(rows, csv_profiles, scenario_data["accounts"], p2m_rows)
    intel_rows = _intelligence_rows()
    grievance = _scenario_grievance(scenarios["D"])

    _write_enriched_csv(output_path, rows)
    print(f"Enriched DEMO DATA CSV: {output_path} ({len(rows)} rows)")
    _seed_database(
        scenarios=scenarios,
        rows=rows,
        csv_profiles=csv_profiles,
        scenario_data=scenario_data,
        sessions=sessions,
        events=events,
        assessments=assessments,
        grievance=grievance,
        intel_rows=intel_rows,
        account_rows=accounts,
        reset=args.reset,
    )
    print("Run verification with: python scripts\\verify_seed.py")


if __name__ == "__main__":
    main()
