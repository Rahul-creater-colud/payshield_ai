import { mockTransactions } from "../data/mockTransactions";
import { mockCollectRequests } from "../data/mockCollectRequests";
import { mockAlerts } from "../data/mockAlerts";
import {
  mockDashboardMetrics,
  mockDailyActivity,
  mockRiskDistribution,
  mockTransactionTypesVolume,
  mockHourlyTraffic
} from "../data/mockAnalytics";
import { mockScreenshotResults } from "../data/mockScreenshotResults";
import { calculateRiskScore } from "../utils/riskCalculators";

// Delays are presentation-only in explicit demo mode.
const delay = (ms = 350) => new Promise((resolve) => setTimeout(resolve, ms));

// In-memory clones to allow mutable actions in mock mode (e.g., accepting/rejecting collect requests, adding analyzed txns)
let activeTransactions = [...mockTransactions];
let activeCollectRequests = [...mockCollectRequests];
let activeAlerts = [...mockAlerts];

export const mockDataService = {
  // Check mock health
  async checkHealth() {
    await delay(150);
    return { status: "healthy", mode: "MOCK_SIMULATION", timestamp: new Date().toISOString() };
  },

  // 1. Transaction analysis
  async analyzeTransaction(formData) {
    await delay(600);
    const evaluation = calculateRiskScore(formData);
    const newTx = {
      id: `tx-${Date.now()}`,
      transactionId: formData.transactionId,
      senderName: formData.senderUpi.split("@")[0].replace(".", " "),
      senderUpi: formData.senderUpi,
      receiverName: formData.receiverUpi.split("@")[0].replace(".", " "),
      receiverUpi: formData.receiverUpi,
      amount: parseFloat(formData.amount),
      timestamp: formData.transactionTime || new Date().toISOString(),
      type: formData.transactionType,
      status: evaluation.status,
      riskScore: evaluation.riskScore,
      riskCategory: evaluation.riskCategory,
      reasons: evaluation.triggers,
      indicators: evaluation.indicators,
      simulated: true,
      data_label: "DEMO DATA — heuristic sample; no payment was processed"
    };

    // Prepend to transaction list
    activeTransactions = [newTx, ...activeTransactions];

    return {
      success: true,
      data: newTx
    };
  },

  // 2. Transaction history with search & filter
  async getTransactions(params = {}) {
    await delay(250);
    let list = [...activeTransactions];

    if (params.search) {
      const q = params.search.toLowerCase().trim();
      list = list.filter(
        (t) =>
          t.transactionId.toLowerCase().includes(q) ||
          t.senderUpi.toLowerCase().includes(q) ||
          t.receiverUpi.toLowerCase().includes(q) ||
          t.senderName.toLowerCase().includes(q) ||
          t.receiverName.toLowerCase().includes(q)
      );
    }

    if (params.status && params.status !== "ALL") {
      list = list.filter((t) => t.status === params.status);
    }

    if (params.riskCategory && params.riskCategory !== "ALL") {
      list = list.filter((t) => t.riskCategory === params.riskCategory);
    }

    return {
      success: true,
      total: list.length,
      data: list
    };
  },

  // 3. Single transaction detail
  async getTransactionDetail(id) {
    await delay(200);
    const item = activeTransactions.find((t) => t.id === id || t.transactionId === id);
    if (!item) {
      throw { message: `Transaction with ID '${id}' not found` };
    }
    return { success: true, data: item };
  },

  // 4. Collect requests list
  async getCollectRequests() {
    await delay(300);
    return {
      success: true,
      total: activeCollectRequests.length,
      data: activeCollectRequests
    };
  },

  // 5. Action on collect request (Accept or Reject)
  async actionCollectRequest(id, action) {
    await delay(400);
    const reqIndex = activeCollectRequests.findIndex((r) => r.id === id);
    if (reqIndex === -1) {
      throw { message: `Collect request '${id}' not found` };
    }

    const updated = {
      ...activeCollectRequests[reqIndex],
      status: action === "ACCEPT" ? "DEMO_APPROVED" : "DEMO_REJECTED",
      actionTimestamp: new Date().toISOString()
    };
    activeCollectRequests[reqIndex] = updated;

    return {
      success: true,
      action,
      data: updated,
      message: `DEMO action only: ${action === "ACCEPT" ? "simulated approval" : "simulated rejection"}; no payment was processed.`
    };
  },

  // 6. Fraud analytics data
  async getFraudAnalytics(filters = {}) {
    await delay(350);
    return {
      success: true,
      metrics: mockDashboardMetrics,
      data_label: "DEMO DATA — synthetic sample statistics",
      dailyActivity: mockDailyActivity,
      riskDistribution: mockRiskDistribution,
      transactionTypes: mockTransactionTypesVolume,
      hourlyTraffic: mockHourlyTraffic,
      updated_at: new Date().toISOString(),
      simulated: true,
      filtersApplied: filters
    };
  },

  // 7. Screenshot OCR & Forensic scan
  async scanScreenshot(file, sampleKey = null) {
    if (file && !sampleKey) {
      throw new Error("Uploaded-image OCR is unavailable. Select a labeled demo sample instead.");
    }
    await delay(250);
    let result;
    if (sampleKey && mockScreenshotResults.sampleScams.some((s) => s.id === sampleKey)) {
      result = mockScreenshotResults.sampleScams.find((s) => s.id === sampleKey);
    } else {
      throw new Error("Select an explicitly labeled demo sample to view its synthetic response.");
    }

    return {
      success: true,
      data_label: "DEMO DATA — synthetic sample response; image not analyzed",
      simulated: true,
      scannedAt: new Date().toISOString(),
      data: result
    };
  },

  // 8. Fraud alerts list
  async getFraudAlerts() {
    await delay(250);
    const summary = {
      totalAlerts: activeAlerts.length,
      highRiskAssessments: activeAlerts.filter((alert) => alert.category === "HIGH").length,
      mediumRiskAssessments: activeAlerts.filter((alert) => alert.category === "MEDIUM").length,
      resolvedAssessments: activeAlerts.filter((alert) => alert.status === "RESOLVED").length,
      fraudPreventedAmount: null,
      payment_provider_integration: false
    };
    return {
      success: true,
      total: activeAlerts.length,
      summary,
      data_label: "DEMO DATA — synthetic sample alerts",
      data: activeAlerts
    };
  },

  // 9. Resolve alert
  async resolveAlert(id, notes) {
    await delay(300);
    activeAlerts = activeAlerts.map((a) =>
      a.id === id ? { ...a, status: "RESOLVED", resolutionNotes: notes, resolvedAt: new Date().toISOString() } : a
    );
    return { success: true, message: `Alert ${id} resolved successfully` };
  }
};
