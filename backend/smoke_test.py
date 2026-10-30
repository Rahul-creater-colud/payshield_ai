"""Quick smoke test - run with: python smoke_test.py"""
import time, os, sys

def main():
    start = time.time()
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.database import Base, get_db
    from app.main import create_app
    from app.db.seed import load_seed
    from app import models  # noqa

    TEST_DB_URL = "sqlite:///./test_smoke.db"
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    load_seed(db=db, seed_path="app/data/seed.json")
    db.close()
    print(f"DB setup: {time.time()-start:.2f}s")

    def override():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override

    failures = []

    def check(label, cond, detail=""):
        if cond:
            print(f"  PASS  {label}")
        else:
            print(f"  FAIL  {label} {detail}")
            failures.append(label)

    with TestClient(app, raise_server_exceptions=False) as client:
        # Health
        r = client.get("/health")
        check("GET /health 200", r.status_code == 200)
        check("health db=ok", r.json().get("db") == "ok")
    
        r = client.get("/api/health")
        check("GET /api/health 200", r.status_code == 200)
    
        # Catalog
        r = client.get("/api/catalog")
        check("GET /api/catalog 200", r.status_code == 200)
        check("catalog simulated=true", r.json().get("simulated") is True)
        scenarios = {s["id"] for s in r.json().get("scenarios", [])}
        check("catalog has scenarios A,B,C,D,LOW", {"A","B","C","D","LOW"} <= scenarios, str(scenarios))
    
        # Risk - LOW
        r = client.post("/api/risk/assess", json={
            "sender_id": "U001", "receiver_id": "ACC_101",
            "amount": 500.0, "request_type": "PAY",
            "context": {"unsolicited": False}
        })
        check("POST /api/risk/assess 200", r.status_code == 200, r.text[:200])
        body = r.json()
        check("low risk category LOW", body.get("category") == "LOW", f"got {body.get('category')} score={body.get('score')}")
        check("low risk simulated=true", body.get("simulated") is True)
        check("low risk has assessment_id", body.get("assessment_id","").startswith("ASM_"))
        check("low risk action=PROCEED", body.get("recommended_action") == "PROCEED")
        asm_id = body.get("assessment_id")
    
        # GET assessment
        r = client.get(f"/api/risk/assessments/{asm_id}")
        check("GET /api/risk/assessments/{id} 200", r.status_code == 200)
    
        r = client.get("/api/risk/assessments?limit=5")
        check("GET /api/risk/assessments list", r.status_code == 200 and isinstance(r.json(), list))
    
        # Risk - Scenario A collect request
        r = client.post("/api/risk/assess", json={
            "sender_id": "U001", "receiver_id": "ACC_150",
            "amount": 2999.0, "request_type": "COLLECT_REQUEST",
            "context": {
                "message_text": "You have received a refund, approve to receive",
                "unsolicited": True,
                "events": ["refund_message", "link_click", "collect_request"]
            }
        })
        check("Scenario A 200", r.status_code == 200, r.text[:200])
        body = r.json()
        check("Scenario A cat MEDIUM/HIGH", body.get("category") in ("MEDIUM","HIGH"), f"got {body.get('category')} score={body.get('score')}")
        check("Scenario A collect_request_warning", body.get("collect_request_warning") is not None)
        pb_names = [p["name"] for p in body.get("playbook_matches", [])]
        check("Scenario A playbook match", any("COLLECT" in n or "REFUND" in n for n in pb_names), str(pb_names))
    
        # Risk - Scenario D (new recipient, must NOT be HIGH)
        r = client.post("/api/risk/assess", json={
            "sender_id": "U001", "receiver_id": "ACC_111",
            "amount": 1000.0, "request_type": "PAY",
            "context": {"unsolicited": False}
        })
        check("Scenario D 200", r.status_code == 200, r.text[:200])
        body = r.json()
        check("Scenario D NOT HIGH", body.get("category") != "HIGH", f"got {body.get('category')} score={body.get('score')}")
    
        # Risk - Scenario B mule
        r = client.post("/api/risk/assess", json={
            "sender_id": "U003", "receiver_id": "ACC_300",
            "amount": 9500.0, "request_type": "PAY",
            "context": {"unsolicited": False}
        })
        check("Scenario B 200", r.status_code == 200, r.text[:200])
        body = r.json()
        check("Scenario B MEDIUM or HIGH", body.get("category") in ("MEDIUM","HIGH"), f"got {body.get('category')} score={body.get('score')}")
    
        # Validation errors
        r = client.post("/api/risk/assess", json={"sender_id":"UNKNOWN","receiver_id":"ACC_101","amount":100.0,"request_type":"PAY"})
        check("Unknown sender 404", r.status_code == 404)
        check("Unknown sender error envelope", "error" in r.json())
    
        r = client.post("/api/risk/assess", json={"sender_id":"U001","receiver_id":"ACC_101","amount":-1.0,"request_type":"PAY"})
        check("Negative amount 422", r.status_code == 422)
        check("422 error envelope", "error" in r.json())
    
        r = client.post("/api/risk/assess", json={"sender_id":"U001","receiver_id":"ACC_101","amount":100.0,"request_type":"PAY","otp":"1234"})
        check("OTP field rejected 422", r.status_code == 422)
    
        # URL scan
        r = client.post("/api/urls/scan", json={"url": "not a url !!!"})
        check("URL invalid 200 not crash", r.status_code == 200)
        check("URL invalid verdict=INVALID", r.json().get("verdict") == "INVALID")
    
        r = client.post("/api/urls/scan", json={"url": "http://paytm-secure.xyz/kyc-update"})
        check("URL lookalike SUSPICIOUS/MALICIOUS", r.json().get("verdict") in ("SUSPICIOUS","MALICIOUS"))
    
        r = client.post("/api/urls/scan", json={"url": "https://paytm-secure.xyz/login"})
        check("HTTPS lookalike NOT SAFE", r.json().get("verdict") != "SAFE")
    
        # Network
        r = client.get("/api/accounts/ACC_300/network")
        check("Network ACC_300 200", r.status_code == 200, r.text[:200])
        body = r.json()
        check("Network simulated=true", body.get("simulated") is True)
        check("Network has patterns", len(body.get("patterns",[])) > 0, str([p["pattern"] for p in body.get("patterns",[])]))
        check("Network FAN_IN in patterns", any(p["pattern"] == "FAN_IN" for p in body.get("patterns",[])))
        check("Network directed edges", all("->" in e.get("direction","") for e in body.get("edges",[])))
    
        r = client.get("/api/accounts/ACC_NOTEXIST/network")
        check("Network unknown 404", r.status_code == 404)
        check("Network 404 error envelope", "error" in r.json())
    
        # Grievances
        r = client.post("/api/grievances", json={
            "user_reference": "U001",
            "assessment_id": asm_id,
            "reason": "I did not authorize this transaction at all"
        })
        check("POST /api/grievances 201", r.status_code == 201, r.text[:200])
        grv = r.json()
        check("Grievance has case_id", grv.get("case_id","").startswith("CASE_"))
        check("Grievance status=SUBMITTED", grv.get("status") == "SUBMITTED")
        check("Grievance disclaimer", "disclaimer" in grv)
        case_id = grv.get("case_id")
    
        r = client.get(f"/api/grievances/{case_id}")
        check("GET /api/grievances/{id} 200", r.status_code == 200)
    
        r = client.get("/api/grievances")
        check("GET /api/grievances list 200", r.status_code == 200)
        check("Grievances list has items+total", "items" in r.json() and "total" in r.json())
    
        r = client.patch(f"/api/grievances/{case_id}", json={"status":"UNDER_REVIEW","reviewer_note":"Investigating"})
        check("PATCH grievance 200", r.status_code == 200, r.text[:200])
        check("PATCH grievance status updated", r.json().get("status") == "UNDER_REVIEW")
        check("PATCH history appended", len(r.json().get("status_history",[])) == 2)
    
        r = client.patch(f"/api/grievances/{case_id}", json={"status":"UNDER_REVIEW"})
        check("PATCH without reviewer_note 422", r.status_code == 422)
    
        # Resolve and test terminal state
        client.patch(f"/api/grievances/{case_id}", json={"status":"RESOLVED","reviewer_note":"Case closed"})
        r = client.patch(f"/api/grievances/{case_id}", json={"status":"UNDER_REVIEW","reviewer_note":"Try reopen"})
        check("PATCH terminal state rejected 400", r.status_code == 400)
    
        # Dashboard
        r = client.get("/api/dashboard/summary")
        check("GET /api/dashboard/summary 200", r.status_code == 200, r.text[:200])
        body = r.json()
        check("Dashboard data_label", body.get("data_label") == "DEMO / SYNTHETIC DATA")
        check("Dashboard simulated=true", body.get("simulated") is True)
        check("Dashboard has totals/risk_distribution", "totals" in body and "risk_distribution" in body)
        check("Dashboard ACC_300 in clusters", any(c["center"] == "ACC_300" for c in body.get("suspicious_clusters",[])))
    
        # Intelligence
        r = client.get("/api/intelligence")
        check("GET /api/intelligence 200", r.status_code == 200)
        body = r.json()
        check("Intelligence total >= 10", body.get("total",0) >= 10, str(body.get("total")))
        check("Intelligence data_label=SYNTHETIC", body.get("data_label") == "SYNTHETIC")
    
        r = client.get("/api/intelligence/IND_001")
        check("GET /api/intelligence/{id} 200", r.status_code == 200)
        check("Intelligence item has related_accounts", "related_accounts" in r.json())
    
        r = client.post("/api/intelligence/report", json={
            "indicator_type": "VPA",
            "indicator_value": "test-fraud@upi",
            "source": "Demo Bank Test",
            "confidence": 0.75
        })
        check("POST /api/intelligence/report 201", r.status_code == 201)
        check("New indicator UNREVIEWED", r.json().get("review_status") == "UNREVIEWED")
        new_ind_id = r.json().get("indicator_id","")
    
        r = client.patch(f"/api/intelligence/{new_ind_id}", json={"review_status":"VERIFIED"})
        check("PATCH /api/intelligence/{id} 200", r.status_code == 200)
        check("Indicator review_status updated", r.json().get("review_status") == "VERIFIED")
    
        r = client.get("/api/intelligence/IND_NOTEXIST")
        check("Intelligence 404", r.status_code == 404)
        check("Intelligence 404 error envelope", "error" in r.json())
    
        # Admin reset
        r = client.post("/api/admin/reset")
        check("POST /api/admin/reset 200", r.status_code == 200, r.text[:200])

    print()
    print(f"{'='*50}")
    print(f"PASSED: {sum(1 for _ in range(0)) + (50 - len(failures))} / 50")
    print(f"FAILED: {len(failures)}")
    for f in failures:
        print(f"  - {f}")

    try:
        os.remove("test_smoke.db")
    except:
        pass

    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
