# 🛡️ UPI Shield AI — Real-Time Digital Payment & UPI Fraud Detection System

> **Hackathon Problem Statement 3.2: Real-Time Fraud Detection for UPI and Digital Payments**  
> **Team Responsibility: Member 3 – Frontend Development & UI/UX Design**

![React](https://img.shields.io/badge/React-18.3-61dafb.svg?logo=react)
![Vite](https://img.shields.io/badge/Vite-5.4-646CFF.svg?logo=vite)
![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg?logo=tailwind-css)
![Recharts](https://img.shields.io/badge/Recharts-2.12-22c55e.svg)
![Status](https://img.shields.io/badge/Hackathon-Production--Ready-blue.svg)

---

## 📌 Project Overview
**UPI Shield AI** is a state-of-the-art fintech web application designed to safeguard Indian digital payment users against sophisticated cyber scams, reverse-debit collect traps, typosquatted VPAs, social engineering lures, and nocturnal mule spikes.

The frontend is built with a dark navy blue, clean white, and high-visibility risk alert palette (Green = Safe, Yellow = Suspicious, Red = Blocked), featuring glassmorphic accents, interactive time-series telemetry, and simulated AI OCR vision for payment receipts.

---

## 🚀 Key Features & 7 Comprehensive Screens

### 1. 📊 Command Center Dashboard (`/`)
- **Key Metrics:** Real-time counters for Total Transactions (148,920+), Safe Transactions (95.6%), Suspicious Flagged (4,890), Blocked Threats (1,650), and Total Fraud Value Prevented (₹1.42 Cr).
- **Time-Series Area Chart:** 7-day volume breakdown across safe, suspicious, and blocked events.
- **Risk Distribution Chart:** Donut chart segmenting transactions into calibrated severity tiers.
- **Recent Transactions Stream:** Real-time feed with one-click forensic inspector modal.
- **Quick Actions:** Instant shortcuts to score new UPIs, view collect warnings, or upload receipts.

### 2. ⚡ Real-Time Transaction Analysis (`/analyze`)
- **Interactive Form:** Fields for UPI Transaction ID, Sender VPA, Receiver VPA, Amount (₹), Timestamp, and Transaction Modality (P2P, P2M, Collect Request, QR Scan, BillPay).
- **One-Click Presets for Demo:** Instant test buttons for *Phishing Collect Trap*, *Nocturnal Crypto Mule*, *Infant Merchant QR*, and *Safe Food Delivery*.
- **AI Scoring Engine:** Real-time risk score gauge (0 to 100), severity badge, and detailed rule breakdown.
- **Loading Radar Animation:** High-tech radar sweep simulating neural graph analysis.

### 3. 🚨 Collect Request Interception Shield (`/collect-requests`)
- **Reverse-Debit Protection:** Educational alert explaining that **accepting a collect request debits money and never receives money**.
- **Pending Requests:** Displays requester identity, requested amount, urgency triggers, and NPCI registry flags.
- **Two-Step Critical Safeguard:** Multi-level confirmation modal preventing accidental authorization of dangerous collect debit requests.
- **Reject & Block Action:** Immediately declines the collect request and logs the VPA with the fraud registry.

### 4. 📈 Fraud Analytics & Vector Telemetry (`/analytics`)
- **Daily Fraud Detection (₹ INR):** Area chart showing financial loss prevented over time.
- **Transaction Volume Trends:** Grouped bar chart comparing safe transactions vs suspicious flags.
- **Safe vs Suspicious Distribution:** Inner-donut visualization of system-wide traffic.
- **Risk Score Distribution:** Horizontal histogram of transactions scoring from 0 to 100.
- **Channel Vulnerability Matrix:** Breakdown of P2P, P2M, Collect, QR, and BBPS channels.
- **Interactive Filters & Export:** Filter by date window (24H, 7D, 30D), transaction channel, and export to JSON/CSV.

### 5. 🗂️ Transaction Audit History (`/history`)
- **Comprehensive Audit Log:** Columns for Transaction ID, Sender VPA, Receiver VPA, Amount (₹), Date/Time, Status, and Risk Score.
- **Dynamic Search:** Instant full-text search across IDs, names, and VPAs.
- **Status Filters:** Filter by `ALL`, `SAFE`, `SUSPICIOUS`, or `BLOCKED`.
- **Forensic Dossier Inspector:** Modal view revealing NPCI bank reference codes, geolocations, and full heuristic indicators.
- **CSV Exporter:** Download full audit logs for regulatory submission.

### 6. 🔍 Evidence & Screenshot AI Scanner (`/screenshot-scanner`)
- **Multi-Format Upload:** Drag-and-drop or select JPG, JPEG, and PNG payment receipts (up to 10 MB).
- **Scanline Laser Animation:** Interactive visual scanning line replicating computer vision OCR.
- **Entity Extraction:** Highlights scam UPI IDs, detected amounts, and social engineering keywords (e.g. "Won ₹4,999 Cashback", "Power disconnected tonight").
- **Sample Scam Presets:** Built-in test samples (*PhonePe Scratchcard Scam*, *Electricity Bill Extortion*, *Genuine D-Mart Invoice*) for effortless hackathon judging.
- **Re-upload & Reset:** Easy controls to clear and re-analyze multiple receipts.

### 7. 🛡️ Security Alerts & Incident Report (`/alerts-report`)
- **24-Hour Threat Summary:** KPI cards for Critical Threats, Medium Alerts, Fraud Prevented, and AI Latency.
- **Mandatory Consumer Directives:** 4 essential safety guidelines to prevent digital payment scams.
- **Severity-Filtered Alerts:** Detailed dossiers with root-cause explanations and required mitigation protocols.
- **Incident Resolution:** Mark alerts as resolved with custom operator notes.
- **Printable Dossier:** Print-optimized styling for regulatory reports and JSON export.

---

## 🔄 Dual API Architecture: Mock Mode & Live API Mode

UPI Shield AI supports both zero-dependency **MOCK SIMULATION** and **LIVE FASTAPI INTEGRATION**:

| Feature | Mock Simulation Mode | Live API Mode |
|---|---|---|
| **Backend Requirement** | None (100% Client-side) | FastAPI at `http://localhost:8000` |
| **Data Generation** | Realistic heuristic models & mutable arrays | Live REST endpoints |
| **Offline Resilience** | Full interactivity guaranteed | Automatic fallback to mock on network fail |
| **UI Indicator** | Blue status pill on top banner | Green (connected) / Red (disconnected) |

Switch between modes using the **Mode Toggle button** on the top status banner or in settings!

---

## 🛠️ Technology Stack
- **Framework:** React.js 18 with Vite
- **Styling:** Tailwind CSS (Navy palette `#0f2038`, `#081120`, `#2563eb`, plus risk colors `#10b981`, `#f59e0b`, `#ef4444`)
- **Routing:** React Router DOM v6
- **Data Visualizations:** Recharts (AreaChart, BarChart, PieChart)
- **Icons:** Lucide React
- **HTTP Client:** Axios with custom interceptors and error normalization

---

## 📦 Installation & Running Instructions

### 1. Prerequisites
- Node.js (v18.0 or higher)
- npm or yarn

### 2. Setup & Installation
```bash
# Navigate to the project directory
cd "C:\Users\VISIONPC\.gemini\antigravity\scratch\upi-fraud-shield"

# Install dependencies (already completed)
npm install
```

### 3. Run Development Server
```bash
npm run dev
```
The application will launch at `http://localhost:5173`.

### 4. Build for Production
```bash
npm run build
npm run preview
```

---

## 🔌 Backend Integration (Python FastAPI)
Refer to [`API_DOCUMENTATION.md`](./API_DOCUMENTATION.md) for full request/response schemas, Pydantic models, and CORS configuration.

To test live backend integration:
1. Start your FastAPI server on `http://localhost:8000`.
2. Toggle the mode switch in the top banner to **LIVE API**.
3. Click **"Ping Backend"** to verify connection.

---

## 👥 Hackathon Team Contribution
- **Member 3 – Frontend Development:** Complete responsive web application, interactive Recharts telemetry, heuristic scoring logic, screenshot scanner with mock OCR, collect request warnings, confirmation modals, toast system, and API service layer.
