export const mockCollectRequests = [
  {
    id: "col-201",
    senderName: "Customer Support Refund Desk",
    senderUpi: "refund-support-desk88@ybl",
    amount: 19500.00,
    requestedAt: "2026-10-30T17:15:00+05:30",
    expiresAt: "2026-10-30T18:15:00+05:30",
    status: "PENDING",
    riskScore: 96,
    riskCategory: "HIGH",
    warningType: "REFUND_IMPERSONATION",
    warningTitle: "Critical Alert: Reverse Debit Phishing Attempt",
    warningMessage: "The requester is pretending to issue a refund or lottery reward, but this is a COLLECT REQUEST that will DEBIT ₹19,500 from your bank account immediately.",
    fraudTriggers: [
      "Fraudulent narrative: Claiming to send a refund via collect request (UPI does not require PIN to receive money)",
      "Sender VPA was registered less than 72 hours ago",
      "Multiple user complaints for fake refund scams associated with this bank node",
      "Urgency trigger: 'Immediate action required within 60 mins'"
    ],
    verifiedMerchant: false,
    recommendedAction: "STOP_REVIEW_RECOMMENDED"
  },
  {
    id: "col-202",
    senderName: "OLX Verification Center",
    senderUpi: "olx-escrow-payment@okaxis",
    amount: 8900.00,
    requestedAt: "2026-10-30T16:45:20+05:30",
    expiresAt: "2026-10-30T17:45:20+05:30",
    status: "PENDING",
    riskScore: 88,
    riskCategory: "HIGH",
    warningType: "MARKETPLACE_ADVANCE_DEBIT",
    warningTitle: "High Danger: Fake Buyer Escrow Collect Request",
    warningMessage: "A buyer claiming to buy your listed item has sent a request asking for ₹8,900 under the pretext of 'escrow advance verification'. You will lose ₹8,900 if you accept.",
    fraudTriggers: [
      "OLX/Quikr buyer reverse scam detected",
      "Non-merchant personal UPI ID disguised with 'escrow' keyword",
      "Payer does not have prior payment history with recipient"
    ],
    verifiedMerchant: false,
    recommendedAction: "STOP_REVIEW_RECOMMENDED"
  },
  {
    id: "col-203",
    senderName: "Dr. Alok Verma Clinic",
    senderUpi: "dr.alokverma@hdfcbank",
    amount: 1200.00,
    requestedAt: "2026-10-30T15:20:10+05:30",
    expiresAt: "2026-10-30T18:20:10+05:30",
    status: "PENDING",
    riskScore: 48,
    riskCategory: "MEDIUM",
    warningType: "FIRST_TIME_INDIVIDUAL_COLLECT",
    warningTitle: "Caution: First-Time Collect Request",
    warningMessage: "This collect request is from a first-time individual payee. Verify that you scheduled this consultation before entering your UPI PIN.",
    fraudTriggers: [
      "New individual payee requesting payment",
      "No historical transactions between sender and receiver",
      "Moderate risk score due to unverified medical billing channel"
    ],
    verifiedMerchant: false,
    recommendedAction: "VERIFY_PAYEE_IDENTITY"
  },
  {
    id: "col-204",
    senderName: "Cult.fit Fitness Centers",
    senderUpi: "cultfit.membership@icici",
    amount: 3499.00,
    requestedAt: "2026-10-30T12:00:00+05:30",
    expiresAt: "2026-10-30T23:59:59+05:30",
    status: "PENDING",
    riskScore: 14,
    riskCategory: "LOW",
    warningType: "DEMO_SAMPLE",
    warningTitle: "Low-Risk Demo Collect Request",
    warningMessage: "Synthetic example only. PayShield did not verify this merchant or collect request.",
    fraudTriggers: [
      "Synthetic demo verification marker; no external merchant checks were performed"
    ],
    verifiedMerchant: false,
    recommendedAction: "REVIEW_ONLY"
  }
];
