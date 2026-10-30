export const mockTransactions = [
  {
    id: "tx-101",
    transactionId: "UPI/2026/894729104",
    senderName: "Aarav Sharma",
    senderUpi: "aarav.sharma@okaxis",
    receiverName: "Kavita Verma",
    receiverUpi: "kavita.v@okhdfcbank",
    amount: 1450.00,
    timestamp: "2026-10-30T17:42:15+05:30",
    type: "P2P",
    status: "SAFE",
    riskScore: 12,
    riskCategory: "LOW",
    reasons: [
      "Frequent contact with verified transaction history",
      "Sender device and geofence consistent with habitual usage",
      "Amount within normal standard deviation for sender"
    ],
    indicators: {
      newDevice: false,
      unusualTime: false,
      velocityAlert: false,
      blacklistedReceiver: false,
      mismatchedVPA: false,
      collectRequestAnomaly: false
    },
    location: "Mumbai, Maharashtra",
    bankRefNumber: "SBI649201948201"
  },
  {
    id: "tx-102",
    transactionId: "UPI/2026/993821034",
    senderName: "Pooja Patel",
    senderUpi: "pooja.patel@icici",
    receiverName: "KYC Verification Support",
    receiverUpi: "sbi-kyc-update-desk@ybl",
    amount: 24999.00,
    timestamp: "2026-10-30T16:15:30+05:30",
    type: "COLLECT_REQUEST",
    status: "STOP_RECOMMENDED",
    riskScore: 94,
    riskCategory: "HIGH",
    reasons: [
      "Impersonation tactic: UPI handle mimics official bank KYC department",
      "Synthetic demo indicator match; no external fraud registry was queried",
      "Reverse debit trick: collect request disguised as refund processing",
      "New beneficiary with high uncharacteristic debit amount"
    ],
    indicators: {
      newDevice: true,
      unusualTime: false,
      velocityAlert: true,
      blacklistedReceiver: true,
      mismatchedVPA: true,
      collectRequestAnomaly: true
    },
    location: "Ahmedabad, Gujarat",
    bankRefNumber: "ICIC839201847192"
  },
  {
    id: "tx-103",
    transactionId: "UPI/2026/774829105",
    senderName: "Vikram Malhotra",
    senderUpi: "vikram.m@paytm",
    receiverName: "Metro Electronics & Gadgets",
    receiverUpi: "metro.gadgets@razorpay",
    amount: 18400.00,
    timestamp: "2026-10-30T14:28:40+05:30",
    type: "QR_SCAN",
    status: "FLAGGED",
    riskScore: 68,
    riskCategory: "MEDIUM",
    reasons: [
      "New merchant QR code created less than 48 hours ago",
      "Amount 4.8x higher than user's 30-day average QR spend",
      "Rapid succession: 2 prior micro-test transactions detected"
    ],
    indicators: {
      newDevice: false,
      unusualTime: false,
      velocityAlert: true,
      blacklistedReceiver: false,
      mismatchedVPA: true,
      collectRequestAnomaly: false
    },
    location: "Bengaluru, Karnataka",
    bankRefNumber: "HDFC920183749210"
  },
  {
    id: "tx-104",
    transactionId: "UPI/2026/663819203",
    senderName: "Sneha Reddy",
    senderUpi: "sneha.reddy@okicici",
    receiverName: "Swiggy Food Delivery",
    receiverUpi: "swiggy.pay@icici",
    amount: 520.00,
    timestamp: "2026-10-30T13:10:05+05:30",
    type: "P2M",
    status: "SAFE",
    riskScore: 8,
    riskCategory: "LOW",
    reasons: [
      "Synthetic demo merchant indicator; no external verification was performed",
      "Routine consumer transaction pattern",
      "Zero fraud signals"
    ],
    indicators: {
      newDevice: false,
      unusualTime: false,
      velocityAlert: false,
      blacklistedReceiver: false,
      mismatchedVPA: false,
      collectRequestAnomaly: false
    },
    location: "Hyderabad, Telangana",
    bankRefNumber: "ICIC993817204918"
  },
  {
    id: "tx-105",
    transactionId: "UPI/2026/554910294",
    senderName: "Rohan Deshmukh",
    senderUpi: "rohan.d@oksbi",
    receiverName: "Tata Power Utilities",
    receiverUpi: "tatapower.bills@billdesk",
    amount: 2850.00,
    timestamp: "2026-10-30T11:45:22+05:30",
    type: "BILL_PAY",
    status: "SAFE",
    riskScore: 15,
    riskCategory: "LOW",
    reasons: [
      "BBPS-certified utility aggregator",
      "Monthly recurring bill payment pattern verified",
      "Standard payer behavior"
    ],
    indicators: {
      newDevice: false,
      unusualTime: false,
      velocityAlert: false,
      blacklistedReceiver: false,
      mismatchedVPA: false,
      collectRequestAnomaly: false
    },
    location: "Pune, Maharashtra",
    bankRefNumber: "SBI748291039482"
  },
  {
    id: "tx-106",
    transactionId: "UPI/2026/443920183",
    senderName: "Ananya Sen",
    senderUpi: "ananya.sen@ybl",
    receiverName: "Telegram Crypto Wealth Bot",
    receiverUpi: "fastpay.crypto99@airtel",
    amount: 45000.00,
    timestamp: "2026-10-30T02:35:10+05:30",
    type: "P2P",
    status: "STOP_RECOMMENDED",
    riskScore: 98,
    riskCategory: "HIGH",
    reasons: [
      "Nocturnal anomaly: transaction initiated during dormant sleeping hours (02:35 AM)",
      "High-risk crypto arbitrage scam pattern matched via NLP clustering",
      "Velocity spike: third max-limit attempt within 15 minutes",
      "Unregistered airtel payments bank VPA with 100% money mule outflow"
    ],
    indicators: {
      newDevice: true,
      unusualTime: true,
      velocityAlert: true,
      blacklistedReceiver: true,
      mismatchedVPA: true,
      collectRequestAnomaly: false
    },
    location: "Kolkata, West Bengal",
    bankRefNumber: "YESB102938475610"
  },
  {
    id: "tx-107",
    transactionId: "UPI/2026/332910485",
    senderName: "Deepak Joshi",
    senderUpi: "deepak.joshi@hdfcbank",
    receiverName: "OLX Buyer Escrow Service",
    receiverUpi: "olx-escrow-security@okaxis",
    amount: 8500.00,
    timestamp: "2026-10-29T19:20:00+05:30",
    type: "COLLECT_REQUEST",
    status: "FLAGGED",
    riskScore: 74,
    riskCategory: "MEDIUM",
    reasons: [
      "Classic marketplace scam: fake escrow account requesting debit",
      "Collect request sender registered as individual rather than merchant entity",
      "Message contains urgent wording: 'Approve now or item release cancelled'"
    ],
    indicators: {
      newDevice: false,
      unusualTime: false,
      velocityAlert: false,
      blacklistedReceiver: false,
      mismatchedVPA: true,
      collectRequestAnomaly: true
    },
    location: "Jaipur, Rajasthan",
    bankRefNumber: "HDFC884920183749"
  },
  {
    id: "tx-108",
    transactionId: "UPI/2026/221940381",
    senderName: "Meera Nair",
    senderUpi: "meera.nair@paytm",
    receiverName: "Apollo Pharmacy",
    receiverUpi: "apollopharmacy@icici",
    amount: 980.00,
    timestamp: "2026-10-29T15:12:45+05:30",
    type: "P2M",
    status: "SAFE",
    riskScore: 10,
    riskCategory: "LOW",
    reasons: [
      "Legitimate healthcare merchant verified with UPI gateway",
      "Typical routine transaction amount",
      "Device security trust score 99/100"
    ],
    indicators: {
      newDevice: false,
      unusualTime: false,
      velocityAlert: false,
      blacklistedReceiver: false,
      mismatchedVPA: false,
      collectRequestAnomaly: false
    },
    location: "Kochi, Kerala",
    bankRefNumber: "PYTM482910394857"
  },
  {
    id: "tx-109",
    transactionId: "UPI/2026/110948372",
    senderName: "Kunal Bansal",
    senderUpi: "kunal.b@oksbi",
    receiverName: "PM Cares Relief Fund (Spoofed)",
    receiverUpi: "pm-relief-fund-2026@ibl",
    amount: 5000.00,
    timestamp: "2026-10-29T10:05:14+05:30",
    type: "QR_SCAN",
    status: "STOP_RECOMMENDED",
    riskScore: 92,
    riskCategory: "HIGH",
    reasons: [
      "Typosquatting fraud: mimics government relief fund handle",
      "VPA reported in cybercrime cell portal for fraudulent charity collections",
      "Receiver bank account is a recently opened mule account"
    ],
    indicators: {
      newDevice: false,
      unusualTime: false,
      velocityAlert: false,
      blacklistedReceiver: true,
      mismatchedVPA: true,
      collectRequestAnomaly: false
    },
    location: "New Delhi, Delhi",
    bankRefNumber: "SBI392019485729"
  },
  {
    id: "tx-110",
    transactionId: "UPI/2026/909182736",
    senderName: "Rajesh Kulkarni",
    senderUpi: "rajesh.k@okhdfcbank",
    receiverName: "Zomato Online Ordering",
    receiverUpi: "zomato@hdfcbank",
    amount: 740.00,
    timestamp: "2026-10-28T20:30:11+05:30",
    type: "P2M",
    status: "SAFE",
    riskScore: 9,
    riskCategory: "LOW",
    reasons: [
      "Verified merchant enterprise with established history",
      "User frequent dining order matching geo profile",
      "Low risk index"
    ],
    indicators: {
      newDevice: false,
      unusualTime: false,
      velocityAlert: false,
      blacklistedReceiver: false,
      mismatchedVPA: false,
      collectRequestAnomaly: false
    },
    location: "Nagpur, Maharashtra",
    bankRefNumber: "HDFC772819304918"
  }
];
