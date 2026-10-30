export const mockDashboardMetrics = {
  totalTransactions: 148920,
  safeTransactions: 142380,
  suspiciousTransactions: 4890,
  blockedTransactions: 0,
  stopReviewRecommendations: 1650,
  assessedTransactions: 148920,
  totalFraudPreventedAmount: null,
  fraudRatePercent: 1.11,
  safeRatePercent: 95.61,
};

export const mockDailyActivity = [
  { day: "Mon", date: "2026-10-24", totalVolume: 18400, safeVolume: 17620, suspiciousVolume: 560, stopReviewVolume: 220 },
  { day: "Tue", date: "2026-10-25", totalVolume: 21200, safeVolume: 20280, suspiciousVolume: 690, stopReviewVolume: 230 },
  { day: "Wed", date: "2026-10-26", totalVolume: 19800, safeVolume: 18940, suspiciousVolume: 610, stopReviewVolume: 250 },
  { day: "Thu", date: "2026-10-27", totalVolume: 23400, safeVolume: 22350, suspiciousVolume: 790, stopReviewVolume: 260 },
  { day: "Fri", date: "2026-10-28", totalVolume: 24900, safeVolume: 23780, suspiciousVolume: 820, stopReviewVolume: 300 },
  { day: "Sat", date: "2026-10-29", totalVolume: 28500, safeVolume: 27150, suspiciousVolume: 980, stopReviewVolume: 370 },
  { day: "Sun", date: "2026-10-30", totalVolume: 22720, safeVolume: 21760, suspiciousVolume: 740, stopReviewVolume: 220 }
];

export const mockRiskDistribution = [
  { range: "0 - 20 (Safe)", count: 128400, color: "#10b981", percent: 86.2 },
  { range: "21 - 40 (Low Risk)", count: 13980, color: "#34d399", percent: 9.4 },
  { range: "41 - 60 (Medium Risk)", count: 3250, color: "#f59e0b", percent: 2.2 },
  { range: "61 - 80 (High Suspicion)", count: 1640, color: "#fb923c", percent: 1.1 },
  { range: "81 - 100 (High Risk)", count: 1650, color: "#ef4444", percent: 1.1 }
];

export const mockTransactionTypesVolume = [
  { type: "P2P (Peer to Peer)", safe: 65400, suspicious: 1890, stopReview: 740, assessed: 68030, total: 68030 },
  { type: "P2M (Merchant Pay)", safe: 52100, suspicious: 920, stopReview: 210, assessed: 53230, total: 53230 },
  { type: "Collect Request", safe: 11400, suspicious: 1680, stopReview: 580, assessed: 13660, total: 13660 },
  { type: "QR Scan", safe: 9800, suspicious: 320, stopReview: 90, assessed: 10210, total: 10210 },
  { type: "Bill Payments (BBPS)", safe: 3680, suspicious: 80, stopReview: 30, assessed: 3790, total: 3790 }
];

export const mockHourlyTraffic = [
  { hour: "00:00", volume: 1200, riskAssessments: 45 },
  { hour: "02:00", volume: 650, riskAssessments: 68 },
  { hour: "04:00", volume: 420, riskAssessments: 52 },
  { hour: "06:00", volume: 1890, riskAssessments: 25 },
  { hour: "08:00", volume: 4800, riskAssessments: 32 },
  { hour: "10:00", volume: 9200, riskAssessments: 78 },
  { hour: "12:00", volume: 11400, riskAssessments: 95 },
  { hour: "14:00", volume: 9800, riskAssessments: 88 },
  { hour: "16:00", volume: 10600, riskAssessments: 112 },
  { hour: "18:00", volume: 13500, riskAssessments: 130 },
  { hour: "20:00", volume: 14200, riskAssessments: 124 },
  { hour: "22:00", volume: 7400, riskAssessments: 80 }
];
