export const mockDashboardMetrics = {
  totalTransactions: 148920,
  safeTransactions: 142380,
  suspiciousTransactions: 4890,
  blockedTransactions: 1650,
  totalFraudPreventedAmount: "₹1,42,85,600",
  fraudRatePercent: 1.11,
  safeRatePercent: 95.61,
  activeMonitoredVpas: 84320,
  systemStatus: "OPTIMAL",
  aiLatencyMs: 38
};

export const mockDailyActivity = [
  { day: "Mon", date: "2026-10-24", totalVolume: 18400, safeVolume: 17620, suspiciousVolume: 560, blockedVolume: 220, fraudPrevented: 185000 },
  { day: "Tue", date: "2026-10-25", totalVolume: 21200, safeVolume: 20280, suspiciousVolume: 690, blockedVolume: 230, fraudPrevented: 210000 },
  { day: "Wed", date: "2026-10-26", totalVolume: 19800, safeVolume: 18940, suspiciousVolume: 610, blockedVolume: 250, fraudPrevented: 240000 },
  { day: "Thu", date: "2026-10-27", totalVolume: 23400, safeVolume: 22350, suspiciousVolume: 790, blockedVolume: 260, fraudPrevented: 295000 },
  { day: "Fri", date: "2026-10-28", totalVolume: 24900, safeVolume: 23780, suspiciousVolume: 820, blockedVolume: 300, fraudPrevented: 380000 },
  { day: "Sat", date: "2026-10-29", totalVolume: 28500, safeVolume: 27150, suspiciousVolume: 980, blockedVolume: 370, fraudPrevented: 420000 },
  { day: "Sun", date: "2026-10-30", totalVolume: 22720, safeVolume: 21760, suspiciousVolume: 740, blockedVolume: 220, fraudPrevented: 310000 }
];

export const mockRiskDistribution = [
  { range: "0 - 20 (Safe)", count: 128400, color: "#10b981", percent: 86.2 },
  { range: "21 - 40 (Low Risk)", count: 13980, color: "#34d399", percent: 9.4 },
  { range: "41 - 60 (Medium Risk)", count: 3250, color: "#f59e0b", percent: 2.2 },
  { range: "61 - 80 (High Suspicion)", count: 1640, color: "#fb923c", percent: 1.1 },
  { range: "81 - 100 (Critical/Blocked)", count: 1650, color: "#ef4444", percent: 1.1 }
];

export const mockTransactionTypesVolume = [
  { type: "P2P (Peer to Peer)", safe: 65400, suspicious: 1890, blocked: 740, total: 68030 },
  { type: "P2M (Merchant Pay)", safe: 52100, suspicious: 920, blocked: 210, total: 53230 },
  { type: "Collect Request", safe: 11400, suspicious: 1680, blocked: 580, total: 13660 },
  { type: "QR Scan", safe: 9800, suspicious: 320, blocked: 90, total: 10210 },
  { type: "Bill Payments (BBPS)", safe: 3680, suspicious: 80, blocked: 30, total: 3790 }
];

export const mockHourlyTraffic = [
  { hour: "00:00", volume: 1200, fraudAttempts: 45 },
  { hour: "02:00", volume: 650, fraudAttempts: 68 },
  { hour: "04:00", volume: 420, fraudAttempts: 52 },
  { hour: "06:00", volume: 1890, fraudAttempts: 25 },
  { hour: "08:00", volume: 4800, fraudAttempts: 32 },
  { hour: "10:00", volume: 9200, fraudAttempts: 78 },
  { hour: "12:00", volume: 11400, fraudAttempts: 95 },
  { hour: "14:00", volume: 9800, fraudAttempts: 88 },
  { hour: "16:00", volume: 10600, fraudAttempts: 112 },
  { hour: "18:00", volume: 13500, fraudAttempts: 130 },
  { hour: "20:00", volume: 14200, fraudAttempts: 124 },
  { hour: "22:00", volume: 7400, fraudAttempts: 80 }
];
