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
      "Review this synthetic assessment; no account controls are available",
      "Recommend independent review; this demo cannot block a beneficiary VPA",
      "Contact the account holder using an independently verified channel",
      "Refer to an authorized fraud response channel outside this demo"
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
    status: "STOP_RECOMMENDED",
    ruleBroken: "R-305: Financial Entity Name Impersonation & Reverse Debit",
    explanation: "A collect request asking for ₹24,999 was sent to the user using the handle 'sbi-kyc-update-desk@ybl'. Scammers often send SMS warnings threatening account freeze unless KYC is verified, followed by a collect request falsely claimed to be a verification deposit.",
    indicators: [
      "VPA handle contains restricted bank trademark keyword 'sbi'",
      "Sender VPA was registered via third-party PSP",
      "Reverse debit trick targeting elderly and non-technical users"
    ],
    recommendedActions: [
      "Review the recorded heuristic indicators before making an independent decision",
      "Verify the VPA with the relevant organization using an independent channel",
      "Do not interpret this synthetic example as a confirmed fraud report"
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
    status: "STOP_RECOMMENDED",
    ruleBroken: "R-401: Typosquatted Philanthropic/Govt VPA",
    explanation: "QR code scam impersonating national relief funds. The handle substitutes the authentic `@sbi` domain with `@ibl` to siphon goodwill donations into an illicit private account.",
    indicators: [
      "Domain similarity distance: 91% match with genuine entity",
      "Recent surge in reported disputes on this handle",
      "Individual name does not match designated trust registration"
    ],
    recommendedActions: [
      "Review this synthetic risk assessment",
      "Use authorized reporting channels if a real incident is independently confirmed",
      "No funds were intercepted or refunded by this demo"
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
      "Review this synthetic risk assessment",
      "Advise user to inspect physical QR sticker for tampering or overlay labels",
      "No settlement controls are available in this demo"
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
      "Review this synthetic assessment before an independent payment decision",
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
      "No punitive action is taken by this demo"
    ]
  }
];
