# PayShield AI – API Contract & Architecture Specification

## Overview
**PayShield AI** is a local, rule-based risk assessment prototype for submitted transaction records. It uses synthetic demo data, has no authorized NPCI/bank/payment-provider integration, does not monitor real UPI traffic, and cannot execute or block real payments. Risk scores are illustrative heuristics, not validated ML output or proof of fraud.

---

## 1. Global Response Standards

### 1.1 Success Responses
* **Direct JSON**: No unnecessary wrapping layers (e.g. `{ "data": ... }`).
* **Simulation Flags**: Endpoints include `"simulated": true` and a disclaimer where relevant:
  ```json
  "disclaimer": "Prototype using synthetic data. Risk scores are illustrative heuristics, not proof of fraud."
  ```

### 1.2 Error Envelope
Every HTTP error (4xx / 5xx) strictly conforms to the envelope:
```json
{
  "error": {
    "code": "VALIDATION_ERROR | NOT_FOUND | BAD_REQUEST | CONFLICT | INTERNAL_ERROR",
    "message": "Human-readable explanation",
    "details": []
  }
}
```

---

## 2. Core Business & Risk Rules

1. **Risk Categories**:
   * **LOW**: `0 – 39` -> Recommended action: `PROCEED`
   * **MEDIUM**: `40 – 69` -> Recommended action: `CAUTION_VERIFY`
   * **HIGH**: `70 – 100` -> Recommended action: `STOP_AND_REVIEW`
2. **New Recipient Rule**: Sending to a new recipient alone must **never** produce a `HIGH` risk score.
3. **Intelligence Retraction**: Intelligence indicators with review status `RETRACTED` are completely ignored in risk calculation.
4. **URL Safety**: HTTPS alone **never** classifies a URL as `SAFE`.
5. **Credential Protection**: Requests containing fields such as `pin`, `otp`, `password`, `card_number`, `cvv`, or `secret` are immediately rejected with `422 Unprocessable Entity`.
6. **Grievance Auditability**: `PATCH /api/grievances/{case_id}` requires `reviewer_note`. Moving a case out of terminal states (`RESOLVED` or `REJECTED`) is rejected with `400 Bad Request`.

---

## 3. Demo Scenarios Supported in Seed Data

* **Scenario A (Fake Collect Request)**: Unsolicited collect request from reported VPA `ACC_150` with refund scam pattern -> Produces `MEDIUM` / `HIGH` risk, fires `collect_request_warning` and `PB_FAKE_COLLECT` / `PB_REFUND_SCAM`.
* **Scenario B (Mule Ring)**: Transfers from feeder accounts `ACC_201..205` funneling into hub `ACC_300` and rapidly distributing to exit accounts `ACC_401..403` -> Fires `FAN_IN`, `FAN_OUT`, `RAPID_ONWARD`, `MULTI_HOP` -> Produces `MEDIUM` / `HIGH` risk.
* **Scenario C (Pending Merchant Session)**: Merchant session `SES_MERCH_001` with expected amount and no matching payment event.
* **Scenario D (Genuine User, New Recipient)**: Regular user sending normal amount to new recipient `ACC_111` -> Produces score `<= MEDIUM` (`LOW` or `MEDIUM`, never `HIGH`).
* **Scenario LOW**: Familiar recipient `ACC_101`, usual amount and usual hour -> `LOW` (`0-39`), action `PROCEED`.

---

## 4. API Endpoints

### 4.1 System & Health
* `GET /health` & `GET /api/health`
  * Returns: `{ "status": "ok", "service": "payshield-backend", "version": "...", "db": "ok", "time": "..." }`
* `GET /api/catalog`
  * Returns demo users, catalog accounts, supported request types, scenario presets, grievance statuses, and indicator types.

### 4.2 Risk Assessment
* `POST /api/risk/assess`
  * Body: `RiskAssessRequest` (`sender_id`, `receiver_id`, `amount`, `request_type`, `context`)
  * Returns: `RiskAssessResponse` (`assessment_id`, `transaction_id`, `score`, `category`, `recommended_action`, `reasons`, `playbook_matches`, `graph_flags`, `layer_scores`, `collect_request_warning`, `simulated`, `disclaimer`)
* `GET /api/risk/assessments`
  * Query: `limit`, `category`
  * Returns list of stored assessments.
* `GET /api/risk/assessments/{assessment_id}`
  * Returns full detail of single assessment.

### 4.3 URL Scanner
* `POST /api/urls/scan`
  * Body: `{"url": "..."}`
  * Performs static heuristic analysis without making outbound network requests.
  * Returns: `verdict` (`SAFE` | `SUSPICIOUS` | `MALICIOUS` | `INVALID`), `risk_score`, `indicators`, `advice`, `simulated`, `disclaimer`.

### 4.4 Graph & Account Network
* `GET /api/accounts/{account_id}/network`
  * Returns ego-graph up to 2 hops: nodes, directed edges, detected patterns (`FAN_IN`, `FAN_OUT`, `RAPID_ONWARD`, `MULTI_HOP`), `legend`, `simulated`, `disclaimer`.

### 4.5 Grievances & Redressal
* `POST /api/grievances`
  * Body: `{"user_reference": "...", "assessment_id": "...", "reason": "...", "evidence_ref": "..."}`
  * Returns `201 Created` with initial status `SUBMITTED` and disclaimer.
* `GET /api/grievances`
  * Query: `status`, `user_reference`, `limit`, `offset`
  * Returns: `{"items": [...], "total": ...}`
* `GET /api/grievances/{case_id}`
  * Returns grievance detail with full `status_history`.
* `PATCH /api/grievances/{case_id}`
  * Body: `{"status": "...", "reviewer_note": "..."}`
  * Appends to `status_history` and updates `updated_at`. Disallows reopening from `RESOLVED` / `REJECTED`.

### 4.6 Dashboard Analytics
* `GET /api/dashboard/summary`
  * Returns an aggregate of stored local records and includes `data_label: "DEMO / SYNTHETIC DATA"`.
* `GET /api/v1/fraud/analytics`
  * Returns counts and chart series derived from stored transactions and latest assessments. `blockedTransactions` requires a verified, non-simulated provider event; `totalFraudPreventedAmount` is `null` unless verified events support a defined calculation.

### 4.7 Fraud Intelligence
* `GET /api/intelligence`
  * Query: `type`, `review_status`, `min_confidence`, `limit`
  * Returns indicator items and total count.
* `GET /api/intelligence/{indicator_id}`
  * Returns indicator details and `related_accounts`.
* `POST /api/intelligence/report`
  * Returns `201 Created` with initial `review_status: "UNREVIEWED"`.
* `PATCH /api/intelligence/{indicator_id}`
  * Updates `review_status` (`VERIFIED`, `DISPUTED`, `RETRACTED`) and notes.

### 4.8 Admin & Recovery
* `POST /api/admin/reset`
  * Guarded by `ENABLE_ADMIN` setting. Drops all tables, re-creates schema, and reloads seed data.
