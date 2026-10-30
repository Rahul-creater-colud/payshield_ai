// Heuristic rule engine used only by the explicit frontend demo mode.

export const SUSPICIOUS_KEYWORDS = [
  "kyc", "verify", "support", "refund", "lottery", "prize", "reward",
  "cashback", "crypto", "escrow", "olx", "airtel-support", "helpdesk",
  "update", "claim", "instant", "telegram", "binance", "giftcard"
];

export const DEMO_SUSPICIOUS_VPAS = [
  "sbi-kyc-update-desk@ybl",
  "fastpay.crypto99@airtel",
  "olx-escrow-security@okaxis",
  "pm-relief-fund-2026@ibl",
  "refund-support-desk88@ybl",
  "reward-win-claim@ybl",
  "discom-bill-sbi@okhdfcbank"
];

export const calculateRiskScore = (data) => {
  let score = 10; // Baseline low risk
  const triggers = [];
  const indicators = {
    keywordAnomaly: false,
    blacklistMatch: false,
    nocturnalHour: false,
    highValueCollect: false,
    newPayeeSpike: false,
    typosquatDomain: false
  };

  const receiverLower = (data.receiverUpi || "").toLowerCase();
  const amount = parseFloat(data.amount) || 0;
  const type = data.transactionType || "P2P";
  const txnTime = data.transactionTime ? new Date(data.transactionTime) : new Date();
  const hour = txnTime.getHours();

  // 1. Blacklist check
  if (DEMO_SUSPICIOUS_VPAS.includes(receiverLower)) {
    score += 75;
    indicators.blacklistMatch = true;
    triggers.push("Receiver matches a synthetic demo indicator; no external registry was queried");
  }

  // 2. Keyword heuristic check
  const matchedKeywords = SUSPICIOUS_KEYWORDS.filter(kw => receiverLower.includes(kw));
  if (matchedKeywords.length > 0) {
    score += 35 * matchedKeywords.length;
    indicators.keywordAnomaly = true;
    triggers.push(`Receiver UPI contains high-risk social engineering keywords: "${matchedKeywords.join(', ')}"`);
  }

  // 3. Collect Request Danger
  if (type === "COLLECT_REQUEST") {
    score += 25;
    triggers.push("Collect Request detected: Approving this requires entering UPI PIN and will DEBIT money, not credit it");
    if (amount >= 5000) {
      score += 25;
      indicators.highValueCollect = true;
      triggers.push(`High amount collect request (₹${amount.toLocaleString('en-IN')}) from unverified counterparty`);
    }
  }

  // 4. Nocturnal hour detection (11 PM to 5 AM)
  if (hour >= 23 || hour <= 5) {
    score += 20;
    indicators.nocturnalHour = true;
    triggers.push(`Nocturnal transaction pattern initiated at ${hour.toString().padStart(2, '0')}:${txnTime.getMinutes().toString().padStart(2, '0')} outside normal active profile hours`);
  }

  // 5. Amount Velocity / High Value
  if (amount > 40000) {
    score += 20;
    indicators.newPayeeSpike = true;
    triggers.push(`High transfer value exceeding typical 90th percentile user peer-to-peer spend threshold`);
  } else if (amount > 15000 && type === "QR_SCAN") {
    score += 18;
    triggers.push("Unusually large single transaction via offline static QR code");
  }

  // Cap score between 3 and 99
  const finalScore = Math.min(Math.max(score, 4), 99);

  let category = "LOW";
  let status = "SAFE";

  if (finalScore >= 70) {
    category = "HIGH";
    status = "STOP_RECOMMENDED";
  } else if (finalScore >= 35) {
    category = "MEDIUM";
    status = "FLAGGED";
  } else {
    category = "LOW";
    status = "SAFE";
    if (triggers.length === 0) {
      triggers.push("No configured local heuristic matched this demo input");
      triggers.push("No external registry or payment provider was consulted");
    }
  }

  return {
    riskScore: finalScore,
    riskCategory: category,
    status,
    triggers,
    indicators,
    evaluatedAt: new Date().toISOString()
  };
};
