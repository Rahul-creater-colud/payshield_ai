export const mockAlerts = [
  {
    id: "alt-501",
    severity: "CRITICAL",
    category: "HIGH",
    riskScore: 98,
    title: "Nocturnal High-Value Outflow to High-Risk Mule Account",
    detectedAt: "2026-10-30T02:35:10+05:30",
    affectedAccount: "ananya.sen@ybl",
    suspectEntity: "fastpay.crypto99@airtel",
    amount: 45000.00,
    status: "INVESTIGATING",
    ruleBroken: "R-702: Nocturnal Unusual Spike + Money Mule Pattern",
    explanation: "A ₹45,000 transaction was initiated at 2:35 AM to a newly provisioned virtual payment address flagged for receiving rapid sequential deposits and immediate crypto off-ramping. The payer's habitual profile shows zero transactions between 11 PM and 6 AM.",
    indicators: [
      "Device IMEI is unrecognised",
      "Velocity: 3 attempts within 15 minutes",
      "Beneficiary UPI handle registered under suspect Airtel Payments Bank node"
    ],
    recommendedActions: [
      "Immediately freeze UPI ID linking for next 24 hours or until biometric step-up",
      "Block beneficiary VPA across all affiliated bank handles",
      "Notify user via out-of-band automated phone verification call",
      "File automated SAR (Suspicious Activity Report) with NPCI central registry"
    ]
  },
  {
    id: "alt-502",
    severity: "CRITICAL",
    category: "HIGH",
    riskScore: 94,
    title: "Bank Impersonation KYC Phishing Collect Request",
    detectedAt: "2026-10-30T16:15:30+05:30",
    affectedAccount: "pooja.patel@icici",
    suspectEntity: "sbi-kyc-update-desk@ybl",
    amount: 24999.00,
    status: "BLOCKED",
    ruleBroken: "R-305: Financial Entity Name Impersonation & Reverse Debit",
    explanation: "A collect request asking for ₹24,999 was sent to the user using the handle 'sbi-kyc-update-desk@ybl'. Scammers often send SMS warnings threatening account freeze unless KYC is verified, followed by a collect request falsely claimed to be a verification deposit.",
    indicators: [
      "VPA handle contains restricted bank trademark keyword 'sbi'",
      "Sender VPA was registered via third-party PSP",
      "Reverse debit trick targeting elderly and non-technical users"
    ],
    recommendedActions: [
      "Permanently blacklist receiver UPI ID across national switch",
      "Alert State Bank of India fraud desk regarding impersonating VPA",
      "Present unskippable full-screen educational prompt to payer"
    ]
  },
  {
    id: "alt-503",
    severity: "HIGH",
    category: "HIGH",
    riskScore: 92,
    title: "Typosquatting Government Relief Fund Spoof",
    detectedAt: "2026-10-29T10:05:14+05:30",
    affectedAccount: "kunal.b@oksbi",
    suspectEntity: "pm-relief-fund-2026@ibl",
    amount: 5000.00,
    status: "BLOCKED",
    ruleBroken: "R-401: Typosquatted Philanthropic/Govt VPA",
    explanation: "QR code scam impersonating national relief funds. The handle substitutes the authentic `@sbi` domain with `@ibl` to siphon goodwill donations into an illicit private account.",
    indicators: [
      "Domain similarity distance: 91% match with genuine entity",
      "Recent surge in reported disputes on this handle",
      "Individual name does not match designated trust registration"
    ],
    recommendedActions: [
      "Submit cybercrime report to 1930 National Helpline API",
      "Auto-refund intercepted funds if held in transit escrow",
      "Revoke QR code terminal ID"
    ]
  },
  {
    id: "alt-504",
    severity: "MEDIUM",
    category: "MEDIUM",
    riskScore: 68,
    title: "Unusual Spend Multiplier at Freshly Minted Merchant QR",
    detectedAt: "2026-10-30T14:28:40+05:30",
    affectedAccount: "vikram.m@paytm",
    suspectEntity: "metro.gadgets@razorpay",
    amount: 18400.00,
    status: "UNDER_REVIEW",
    ruleBroken: "R-504: Transaction Volume Anomaly on Infant Merchant ID",
    explanation: "User scanned a static QR code at an electronics outlet that was created less than 48 hours ago. The amount represents 4.8 times the user's typical daily offline QR spending threshold.",
    indicators: [
      "Infant merchant terminal (< 48 hrs uptime)",
      "High value transaction relative to profile average",
      "Geographical location differs from customary neighborhood pattern"
    ],
    recommendedActions: [
      "Prompt secondary SMS OTP verification in banking app",
      "Advise user to inspect physical QR sticker for tampering or overlay labels",
      "Hold settlement for 6 hours pending merchant delivery confirmation"
    ]
  },
  {
    id: "alt-505",
    severity: "MEDIUM",
    category: "MEDIUM",
    riskScore: 55,
    title: "Rapid Micro-Transaction Probing Followed by High Value",
    detectedAt: "2026-10-29T18:40:12+05:30",
    affectedAccount: "deepak.joshi@hdfcbank",
    suspectEntity: "olx-escrow-security@okaxis",
    amount: 8500.00,
    status: "INVESTIGATING",
    ruleBroken: "R-202: Carding / UPI Balance Probing Sequence",
    explanation: "Account observed two micro payments of ₹1 and ₹2 immediately followed by an ₹8,500 collect request. This ping-probing behavior is a staple indicator of balance testing by malicious actors.",
    indicators: [
      "Sequential testing behavior detected within 3 minute window",
      "Suspicious keywords 'escrow-security' in personal UPI ID"
    ],
    recommendedActions: [
      "Enforce mandatory cool-off period of 15 minutes before authorization",
      "Request user acknowledgement of collect request implications"
    ]
  },
  {
    id: "alt-506",
    severity: "LOW",
    category: "LOW",
    riskScore: 24,
    title: "Unusual Geographical Login with Normal Payment Amount",
    detectedAt: "2026-10-28T09:12:00+05:30",
    affectedAccount: "priya.n@icici",
    suspectEntity: "irctc.tickets@icici",
    amount: 1420.00,
    status: "RESOLVED",
    ruleBroken: "R-101: Geolocation Discrepancy",
    explanation: "User booked railway tickets from an IP located in Delhi whereas customary home location is Chennai. Verified safe due to matching traveler name and ticket PNR issuance.",
    indicators: [
      "Location mismatch (Flight/Travel legitimate)",
      "Trusted merchant (IRCTC)",
      "User confirmed activity via in-app challenge"
    ],
    recommendedActions: [
      "No punitive action required; update traveler transit profile"
    ]
  }
];

export const mockRiskReportSummary = {
  totalAlertsToday: 18,
  criticalHighAlerts: 6,
  mediumAlerts: 8,
  lowAlerts: 4,
  fraudPreventedAmount: "₹4,82,450",
  avgDetectionLatencyMs: 34,
  modelConfidenceScore: "98.4%",
  topVector: "Phishing Collect Requests (52%)",
  safeguardRecommendations: [
    "Never enter your UPI PIN to RECEIVE money or claim cashbacks.",
    "Always examine the merchant display name vs the handle before scanning QR codes in public places.",
    "Be skeptical of urgent calls or SMS insisting on instant KYC renewal or SIM verification.",
    "Set a daily UPI limit in your banking app to cap potential accidental exposure."
  ]
};
