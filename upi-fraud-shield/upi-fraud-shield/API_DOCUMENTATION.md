# 🛡️ UPI Shield AI — Backend Integration & API Contract Documentation
**Problem Statement 3.2: Real-Time Fraud Detection for UPI & Digital Payments**  
**Role:** Member 3 – Frontend Lead  
**Target Backend Framework:** Python FastAPI (Uvicorn)

---

## 1. Overview & Architecture
This document details the RESTful API endpoints, request schemas, response models, and status codes designed for seamless integration between the **React.js Frontend** and the **FastAPI Python Backend**.

The frontend includes a toggle switch between **MOCK SIMULATION MODE** and **LIVE API MODE**.
When live mode is enabled, all requests are routed to the base URL configured in `.env`:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_ENABLE_MOCK_FALLBACK=true
```

---

## 2. Fast API CORS Setup (Backend Team Action Item)
Please ensure FastAPI is configured with the following CORS middleware in `main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="UPI Fraud Detection AI API", version="1.0.0")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 3. API Endpoints Specification

### Endpoint 1: Health & Connectivity Check
- **Route:** `GET /api/v1/health`
- **Description:** Verifies that the FastAPI engine is running and threat models are loaded.
- **Response `200 OK`:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "ai_model": "UPI-Threat-Transformer-v4.2",
  "threat_db_records": 482900,
  "timestamp": "2026-10-30T17:42:00Z"
}
```

---

### Endpoint 2: Real-Time Transaction Risk Analysis
- **Route:** `POST /api/v1/fraud/analyze`
- **Description:** Real-time risk scoring for an incoming or outbound UPI transaction.
- **Request Body (`application/json`):**
```json
{
  "transaction_id": "UPI/2026/894729104",
  "sender_upi": "aarav.sharma@okaxis",
  "receiver_upi": "sbi-kyc-update-desk@ybl",
  "amount": 24999.00,
  "transaction_time": "2026-10-30T16:15:30+05:30",
  "transaction_type": "COLLECT_REQUEST"
}
```
- **Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "transactionId": "UPI/2026/894729104",
    "senderName": "Aarav Sharma",
    "senderUpi": "aarav.sharma@okaxis",
    "receiverName": "KYC Verification Support",
    "receiverUpi": "sbi-kyc-update-desk@ybl",
    "amount": 24999.00,
    "timestamp": "2026-10-30T16:15:30+05:30",
    "type": "COLLECT_REQUEST",
    "status": "BLOCKED",
    "riskScore": 94,
    "riskCategory": "HIGH",
    "reasons": [
      "Impersonation tactic: UPI handle mimics official bank KYC department",
      "VPA handle reported in NPCI fraud registry (7 recent consumer disputes)",
      "Reverse debit trick: collect request disguised as refund processing",
      "New beneficiary with high uncharacteristic debit amount"
    ],
    "indicators": {
      "newDevice": true,
      "unusualTime": false,
      "velocityAlert": true,
      "blacklistedReceiver": true,
      "mismatchedVPA": true,
      "collectRequestAnomaly": true
    },
    "location": "Ahmedabad, Gujarat",
    "bankRefNumber": "ICIC839201847192"
  }
}
```

---

### Endpoint 3: Transaction History Log
- **Route:** `GET /api/v1/transactions`
- **Query Parameters:**
  - `search` (string, optional): Search by Txn ID, VPA or payee name
  - `status` (string, optional): `ALL`, `SAFE`, `SUSPICIOUS`, `BLOCKED`
  - `limit` (integer, default: 50)
- **Response `200 OK`:**
```json
{
  "success": true,
  "total": 10,
  "data": [
    {
      "id": "tx-101",
      "transactionId": "UPI/2026/894729104",
      "senderName": "Aarav Sharma",
      "senderUpi": "aarav.sharma@okaxis",
      "receiverName": "Kavita Verma",
      "receiverUpi": "kavita.v@okhdfcbank",
      "amount": 1450.00,
      "timestamp": "2026-10-30T17:42:15+05:30",
      "type": "P2P",
      "status": "SAFE",
      "riskScore": 12,
      "riskCategory": "LOW",
      "reasons": ["Frequent contact with verified transaction history"]
    }
  ]
}
```

---

### Endpoint 4: Collect Request Interception Shield
- **Route:** `GET /api/v1/collect-requests`
- **Description:** Returns pending collect requests flagged by threat intelligence.
- **Response `200 OK`:**
```json
{
  "success": true,
  "total": 4,
  "data": [
    {
      "id": "col-201",
      "senderName": "Customer Support Refund Desk",
      "senderUpi": "refund-support-desk88@ybl",
      "amount": 19500.00,
      "requestedAt": "2026-10-30T17:15:00+05:30",
      "status": "PENDING",
      "riskScore": 96,
      "riskCategory": "HIGH",
      "warningTitle": "Critical Alert: Reverse Debit Phishing Attempt",
      "warningMessage": "The requester is pretending to issue a refund or lottery reward...",
      "fraudTriggers": [
        "Fraudulent narrative: Claiming to send refund via collect request",
        "Sender VPA was registered less than 72 hours ago"
      ]
    }
  ]
}
```

---

### Endpoint 5: Action Collect Request (Accept / Reject)
- **Route:** `POST /api/v1/collect-requests/{id}/action`
- **Request Body:**
```json
{
  "action": "REJECT" // or "ACCEPT"
}
```
- **Response `200 OK`:**
```json
{
  "success": true,
  "action": "REJECT",
  "message": "Collect request rejected. Requester VPA has been flagged to fraud desk."
}
```

---

### Endpoint 6: Fraud Analytics & Time Series
- **Route:** `GET /api/v1/fraud/analytics`
- **Query Parameters:**
  - `dateRange`: `24H`, `7D`, `30D`
  - `txnType`: `ALL`, `P2P`, `P2M`, `COLLECT_REQUEST`, `QR_SCAN`
- **Response `200 OK`:**
```json
{
  "success": true,
  "metrics": {
    "totalTransactions": 148920,
    "safeTransactions": 142380,
    "suspiciousTransactions": 4890,
    "blockedTransactions": 1650,
    "totalFraudPreventedAmount": "₹1,42,85,600"
  },
  "dailyActivity": [
    { "day": "Mon", "totalVolume": 18400, "safeVolume": 17620, "suspiciousVolume": 560, "blockedVolume": 220, "fraudPrevented": 185000 }
  ],
  "riskDistribution": [
    { "range": "0 - 20 (Safe)", "count": 128400, "color": "#10b981", "percent": 86.2 }
  ]
}
```

---

### Endpoint 7: Evidence & Screenshot AI OCR
- **Route:** `POST /api/v1/fraud/screenshot-ocr`
- **Content-Type:** `multipart/form-data`
- **Form Fields:**
  - `image`: Binary file (JPG/JPEG/PNG)
  - `sample_key`: (optional string)
- **Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "filename": "scam_receipt.png",
    "verdict": "MALICIOUS PHISHING & REVERSE DEBIT SCAM",
    "riskScore": 97,
    "riskCategory": "HIGH",
    "summary": "This image contains high-probability deceptive social engineering tactics...",
    "ocrExtractedText": "CONGRATULATIONS! You have won ₹4,999 Cashback...",
    "extractedEntities": {
      "suspiciousUpiIds": ["reward-win-claim@ybl"],
      "flaggedKeywords": ["won ₹4,999 Cashback", "Pay to claim"],
      "detectedAmount": "₹4,999.00",
      "claimedSender": "PhonePe Festive Rewards (Spoofed)"
    },
    "forensicFindings": [
      {
        "rule": "OCR-01: Cashback Advance Payment Lure",
        "severity": "HIGH",
        "detail": "NPCI and banks NEVER require users to send money or approve requests to receive cashback."
      }
    ],
    "safetyAction": "Do NOT scan QR code or enter your UPI PIN. Report to 1930."
  }
}
```

---

### Endpoint 8: Fraud Alerts & Dossiers
- **Route:** `GET /api/v1/fraud/alerts`
- **Response `200 OK`:**
```json
{
  "success": true,
  "total": 6,
  "summary": {
    "totalAlertsToday": 18,
    "criticalHighAlerts": 6,
    "mediumAlerts": 8,
    "lowAlerts": 4,
    "fraudPreventedAmount": "₹4,82,450",
    "avgDetectionLatencyMs": 34,
    "modelConfidenceScore": "98.4%",
    "topVector": "Phishing Collect Requests (52%)"
  },
  "data": [
    {
      "id": "alt-501",
      "severity": "CRITICAL",
      "category": "HIGH",
      "riskScore": 98,
      "title": "Nocturnal High-Value Outflow to High-Risk Mule Account",
      "affectedAccount": "ananya.sen@ybl",
      "suspectEntity": "fastpay.crypto99@airtel",
      "amount": 45000.00,
      "status": "INVESTIGATING",
      "ruleBroken": "R-702: Nocturnal Spike + Mule Pattern",
      "explanation": "A ₹45,000 transaction was initiated at 2:35 AM...",
      "recommendedActions": [
        "Immediately freeze UPI ID linking for next 24 hours",
        "Block beneficiary VPA across all affiliated bank handles"
      ]
    }
  ]
}
```
