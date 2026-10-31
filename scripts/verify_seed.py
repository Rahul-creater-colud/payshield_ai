#!/usr/bin/env python
"""Verify enriched demo CSV, scenario records, and the active PayShield database."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
DEFAULT_CSV = (
    ROOT / "ml_model" / "ml_model" / "data" / "enriched_indian_upi_fraud_data.csv"
)
SCENARIO_DIR = ROOT / "data" / "scenarios"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument(
        "--expected-fraud-rate",
        type=float,
        default=0.025,
        help="Expected target rate used by enrich_and_seed.py (default: 0.025).",
    )
    parser.add_argument("--database-url", help="Override DB_URL for this verification.")
    args = parser.parse_args()
    if args.database_url:
        os.environ["DB_URL"] = args.database_url
    return args


def _path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _check(condition: bool, message: str, failures: list[str]) -> None:
    marker = "PASS" if condition else "FAIL"
    print(f"[{marker}] {message}")
    if not condition:
        failures.append(message)


def _read_json_scenarios() -> dict[str, dict]:
    result: dict[str, dict] = {}
    for path in sorted(SCENARIO_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
        result[data["scenario_id"]] = data
    return result


def main() -> int:
    args = _parse_args()
    csv_path = _path(args.csv)
    if not csv_path.is_file():
        print(f"[FAIL] Enriched CSV missing: {csv_path}")
        return 1

    with csv_path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        headers = reader.fieldnames or []
    failures: list[str] = []
    required = {
        "TransactionID",
        "UserID",
        "TransactionType",
        "txn_per_day",
        "PhoneNumber",
        "PhoneNumberLabel",
        "Latitude",
        "Longitude",
        "receiver_id",
        "receiver_vpa",
        "request_type",
        "session_id",
        "FraudFlag",
        "FraudPattern",
        "data_label",
    }
    _check(required <= set(headers), "Enriched CSV has all required columns", failures)
    _check(len(rows) == 10017, f"CSV row count is 10,017 (found {len(rows)})", failures)

    fraud_rows = [row for row in rows if row.get("FraudFlag", "").lower() == "true"]
    fraud_rate = len(fraud_rows) / len(rows) if rows else 0
    _check(
        abs(fraud_rate - args.expected_fraud_rate) <= 0.005 + 1 / max(len(rows), 1),
        f"Fraud rate {fraud_rate:.3%} matches configured {args.expected_fraud_rate:.3%}",
        failures,
    )
    phones = [row.get("PhoneNumber", "") for row in rows]
    _check(
        all(len(phone) == 10 and phone[0] in "6789" and phone.isdigit() for phone in phones)
        and len(set(phones)) == len(phones),
        "Phone numbers are unique 10-digit synthetic Indian mobile-format values",
        failures,
    )
    _check(
        all(row.get("PhoneNumberLabel") == "SYNTHETIC" for row in rows),
        "PhoneNumberLabel is SYNTHETIC for every row",
        failures,
    )
    try:
        indian_coordinates = all(
            6.0 <= float(row["Latitude"]) <= 38.0
            and 68.0 <= float(row["Longitude"]) <= 98.0
            for row in rows
        )
    except (KeyError, ValueError):
        indian_coordinates = False
    _check(indian_coordinates, "All coordinates fall within Indian bounds", failures)
    _check(
        all(row["txn_per_day"].isdigit() for row in rows),
        "txn_per_day values are integers; TransactionFrequency was normalized",
        failures,
    )
    _check(
        "TransactionFrequency" not in headers,
        "Obsolete TransactionFrequency text column is absent",
        failures,
    )
    _check(
        all(row["data_label"] == "DEMO DATA" for row in rows),
        "Every enriched record is labeled DEMO DATA",
        failures,
    )
    _check(
        all(
            row["TransactionType"] == "P2M" or not row["session_id"]
            for row in rows
        ),
        "Only P2M transactions have merchant session IDs",
        failures,
    )
    _check(
        all(row["request_type"] in {"PAY", "COLLECT"} for row in rows),
        "CSV request_type values use PAY/COLLECT labels",
        failures,
    )
    _check(
        all(
            row["TransactionType"] != "P2M" or row["request_type"] == "PAY"
            for row in rows
        ),
        "P2M transactions consistently use request_type PAY",
        failures,
    )
    new_recipient_genuine = [
        row
        for row in rows
        if row["IsNewRecipient"] == "True"
        and row["FraudFlag"] == "False"
        and row["FraudPattern"] == "GENUINE_NEW_RECIPIENT"
    ]
    _check(
        bool(new_recipient_genuine),
        f"Genuine new-recipient false-positive examples exist ({len(new_recipient_genuine)})",
        failures,
    )
    night_cases = [
        row
        for row in rows
        if row["FraudPattern"] == "NIGHT_HIGH_AMOUNT_NEW_DEVICE_FAILED_ATTEMPTS"
    ]
    _check(
        len(night_cases) >= 20
        and all(
            datetime.fromisoformat(row["Timestamp"]).hour in {2, 3, 4}
            and float(row["Amount"]) >= 25000
            and row["NewDevice"] == "True"
            and int(row["FailedAttempts"]) >= 3
            and row["FraudFlag"] == "True"
            for row in night_cases
        ),
        f"Night/high-amount/new-device/failed-attempt labels are consistent ({len(night_cases)})",
        failures,
    )

    scenarios = _read_json_scenarios()
    _check(set(scenarios) == {"A", "B", "C", "D"}, "Four scenario JSON files exist", failures)

    os.chdir(BACKEND_ROOT)
    sys.path.insert(0, str(BACKEND_ROOT))
    from sqlalchemy import func
    from app import models
    from app.database import SessionLocal, engine
    from app.services.graph_service import get_account_network

    print(f"Verifying active SQLAlchemy database: {engine.url}")
    db = SessionLocal()
    try:
        csv_transactions = (
            db.query(models.Transaction)
            .filter(models.Transaction.transaction_id.like("CSV_TX_%"))
            .count()
        )
        scenario_transactions = [
            item
            for item in db.query(models.Transaction).all()
            if item.transaction_id.startswith("DEMO_SCENARIO_")
        ]
        _check(csv_transactions == 10000, f"Database CSV transaction rows: {csv_transactions}/10,000", failures)
        _check(
            len(scenario_transactions) == 17,
            f"Database A/B/D scenario transactions: {len(scenario_transactions)}/17",
            failures,
        )
        _check(
            db.query(models.DemoUser).filter(models.DemoUser.user_id.like("CSVU_%")).count()
            == 10000,
            "Database contains all 10,000 CSV demo users",
            failures,
        )
        _check(
            db.query(models.FraudIntelligence)
            .filter(models.FraudIntelligence.indicator_id.like("DEMO_INTEL_%"))
            .count()
            == 100,
            "Database contains 100 synthetic VPA/phone/URL/domain indicators",
            failures,
        )
        session_rows = (
            db.query(models.MerchantSession)
            .filter(models.MerchantSession.session_id.like("DEMO_SESSION_%"))
            .all()
        )
        event_rows = (
            db.query(models.PaymentEvent)
            .filter(models.PaymentEvent.event_id.like("DEMO_EVENT_%"))
            .all()
        )
        _check(len(session_rows) == 30, f"Database merchant sessions: {len(session_rows)}/30", failures)
        _check(
            len(event_rows) == 29 and all(event.simulated is True for event in event_rows),
            f"Database simulated payment events: {len(event_rows)}/29",
            failures,
        )

        scenario_a = scenarios["A"]
        transaction_a = db.get(models.Transaction, scenario_a["transaction_id"])
        assessment_a = db.get(models.RiskAssessment, "DEMO_SCENARIO_A_ASSESSMENT")
        _check(
            transaction_a is not None
            and transaction_a.request_type == "COLLECT_REQUEST"
            and transaction_a.status == "FLAGGED"
            and assessment_a is not None
            and assessment_a.category == "HIGH",
            "Scenario A fake collect request and high-risk assessment exist",
            failures,
        )

        scenario_b = scenarios["B"]
        incoming = (
            db.query(models.GraphEdge)
            .filter(models.GraphEdge.target_account == scenario_b["hub_id"])
            .all()
        )
        incoming_demo = [
            edge for edge in incoming if edge.transaction_id and edge.transaction_id.startswith("DEMO_SCENARIO_B_FEED_")
        ]
        distinct_senders = {edge.source_account for edge in incoming_demo}
        network = get_account_network(db, scenario_b["hub_id"], depth=3)
        pattern_names = {item["pattern"] for item in network["patterns"]} if network else set()
        _check(
            len(distinct_senders) >= 10,
            f"Scenario B has {len(distinct_senders)} distinct senders feeding the mule hub",
            failures,
        )
        _check(
            {"FAN_IN", "RAPID_ONWARD", "MULTI_HOP"} <= pattern_names,
            f"Scenario B graph patterns include fan-in, rapid onward, and multi-hop ({sorted(pattern_names)})",
            failures,
        )
        chain = scenario_b["hop_chain"]
        chain_edges = [
            db.query(models.GraphEdge)
            .filter(
                models.GraphEdge.source_account == source,
                models.GraphEdge.target_account == target,
            )
            .first()
            for source, target in zip(chain, chain[1:])
        ]
        _check(
            all(chain_edges)
            and all(edge.transaction_id.startswith(scenario_b["onward_transaction_prefix"]) for edge in chain_edges),
            "Scenario B contains its full four-account onward chain",
            failures,
        )

        scenario_c = scenarios["C"]
        pending = db.get(models.MerchantSession, scenario_c["session_id"])
        matching_events = (
            db.query(models.PaymentEvent)
            .filter(models.PaymentEvent.session_id == scenario_c["session_id"])
            .count()
        )
        _check(
            pending is not None
            and pending.status == "PENDING"
            and matching_events == 0
            and scenario_c["matching_payment_event"] is False,
            "Scenario C remains PENDING with no matching ledger event",
            failures,
        )

        scenario_d = scenarios["D"]
        transaction_d = db.get(models.Transaction, scenario_d["transaction_id"])
        assessment_d = db.get(models.RiskAssessment, scenario_d["grievance_assessment_id"])
        grievance = db.get(models.Grievance, scenario_d["grievance_case_id"])
        _check(
            transaction_d is not None
            and assessment_d is not None
            and assessment_d.category == "MEDIUM"
            and not scenario_d["fraud_flag"]
            and scenario_d["is_new_recipient"],
            "Scenario D is a genuine new-recipient transaction with a MEDIUM assessment",
            failures,
        )
        _check(
            grievance is not None
            and grievance.status == "SUBMITTED"
            and grievance.assessment_id == scenario_d["grievance_assessment_id"],
            "Scenario D grievance references its stored assessment",
            failures,
        )
        _check(
            db.query(func.count(models.Transaction.transaction_id)).scalar() >= 10017,
            "Existing transactions were preserved alongside seeded records",
            failures,
        )
    finally:
        db.close()

    if failures:
        print(f"Seed verification failed: {len(failures)} check(s).")
        return 1
    print("Seed verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
