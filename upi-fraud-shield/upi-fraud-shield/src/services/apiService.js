import apiClient from "../api/axiosClient";
import { ENDPOINTS } from "../api/endpoints";
import { mockDataService } from "./mockDataService";

// Helper to determine active mode from localStorage or defaults
export const getStoredApiMode = () => {
  const saved = localStorage.getItem("UPI_SHIELD_API_MODE");
  return saved ? saved : "LIVE";
};

export const setStoredApiMode = (mode) => {
  localStorage.setItem("UPI_SHIELD_API_MODE", mode);
};

export const apiService = {
  // Test backend connectivity
  async pingBackend() {
    try {
      const res = await apiClient.get(ENDPOINTS.HEALTH);
      return { connected: true, data: res };
    } catch (err) {
      return { connected: false, error: err.message || "Failed to connect to FastAPI backend" };
    }
  },

  // 1. Transaction Analysis
  async analyzeTransaction(formData, mode = getStoredApiMode()) {
    if (mode === "LIVE") {
      try {
        const response = await apiClient.post(ENDPOINTS.ANALYZE_TRANSACTION, {
          transaction_id: formData.transactionId,
          sender_upi: formData.senderUpi,
          receiver_upi: formData.receiverUpi,
          amount: parseFloat(formData.amount),
          transaction_time: formData.transactionTime || new Date().toISOString(),
          transaction_type: formData.transactionType
        });
        return { source: "LIVE_API", data: response.data || response };
      } catch (err) {
        console.warn("[Live API Error] Falling back or bubbling:", err);
        if (import.meta.env.VITE_ENABLE_MOCK_FALLBACK !== "false") {
          const mockRes = await mockDataService.analyzeTransaction(formData);
          return { source: "MOCK_FALLBACK", data: mockRes.data, error: err.message };
        }
        throw err;
      }
    }
    const mockRes = await mockDataService.analyzeTransaction(formData);
    return { source: "MOCK_MODE", data: mockRes.data };
  },

  // 2. Transaction History
  async getTransactions(params = {}, mode = getStoredApiMode()) {
    if (mode === "LIVE") {
      try {
        const response = await apiClient.get(ENDPOINTS.TRANSACTIONS, { params });
        return { source: "LIVE_API", data: response.data || response };
      } catch (err) {
        console.warn("[Live API Error] Transactions fallback:", err);
        const mockRes = await mockDataService.getTransactions(params);
        return { source: "MOCK_FALLBACK", data: mockRes.data, total: mockRes.total, error: err.message };
      }
    }
    const mockRes = await mockDataService.getTransactions(params);
    return { source: "MOCK_MODE", data: mockRes.data, total: mockRes.total };
  },

  // 3. Transaction Detail
  async getTransactionDetail(id, mode = getStoredApiMode()) {
    if (mode === "LIVE") {
      try {
        const response = await apiClient.get(ENDPOINTS.TRANSACTION_DETAIL(id));
        return { source: "LIVE_API", data: response.data || response };
      } catch (err) {
        const mockRes = await mockDataService.getTransactionDetail(id);
        return { source: "MOCK_FALLBACK", data: mockRes.data };
      }
    }
    const mockRes = await mockDataService.getTransactionDetail(id);
    return { source: "MOCK_MODE", data: mockRes.data };
  },

  // 4. Collect Requests
  async getCollectRequests(mode = getStoredApiMode()) {
    if (mode === "LIVE") {
      try {
        const response = await apiClient.get(ENDPOINTS.COLLECT_REQUESTS);
        return { source: "LIVE_API", data: response.data || response };
      } catch (err) {
        const mockRes = await mockDataService.getCollectRequests();
        return { source: "MOCK_FALLBACK", data: mockRes.data, total: mockRes.total };
      }
    }
    const mockRes = await mockDataService.getCollectRequests();
    return { source: "MOCK_MODE", data: mockRes.data, total: mockRes.total };
  },

  // 5. Action Collect Request (Accept or Reject)
  async actionCollectRequest(id, action, mode = getStoredApiMode()) {
    if (mode === "LIVE") {
      try {
        const response = await apiClient.post(ENDPOINTS.COLLECT_REQUEST_ACTION(id), { action });
        return { source: "LIVE_API", ...response };
      } catch (err) {
        const mockRes = await mockDataService.actionCollectRequest(id, action);
        return { source: "MOCK_FALLBACK", ...mockRes };
      }
    }
    const mockRes = await mockDataService.actionCollectRequest(id, action);
    return { source: "MOCK_MODE", ...mockRes };
  },

  // 6. Fraud Analytics
  async getFraudAnalytics(filters = {}, mode = getStoredApiMode()) {
    if (mode === "LIVE") {
      try {
        const response = await apiClient.get(ENDPOINTS.FRAUD_ANALYTICS, { params: filters });
        return { source: "LIVE_API", data: response.data || response };
      } catch (err) {
        const mockRes = await mockDataService.getFraudAnalytics(filters);
        return { source: "MOCK_FALLBACK", ...mockRes };
      }
    }
    const mockRes = await mockDataService.getFraudAnalytics(filters);
    return { source: "MOCK_MODE", ...mockRes };
  },

  // 7. Screenshot OCR & Fraud Scan
  async scanScreenshot(file, sampleKey = null, mode = getStoredApiMode()) {
    if (mode === "LIVE") {
      try {
        const formData = new FormData();
        if (file) formData.append("image", file);
        if (sampleKey) formData.append("sample_key", sampleKey);

        const response = await apiClient.post(ENDPOINTS.SCREENSHOT_SCAN, formData, {
          headers: { "Content-Type": "multipart/form-data" }
        });
        return { source: "LIVE_API", data: response.data || response };
      } catch (err) {
        const mockRes = await mockDataService.scanScreenshot(file, sampleKey);
        return { source: "MOCK_FALLBACK", ...mockRes };
      }
    }
    const mockRes = await mockDataService.scanScreenshot(file, sampleKey);
    return { source: "MOCK_MODE", ...mockRes };
  },

  // 8. Fraud Alerts
  async getFraudAlerts(mode = getStoredApiMode()) {
    if (mode === "LIVE") {
      try {
        const response = await apiClient.get(ENDPOINTS.FRAUD_ALERTS);
        return { source: "LIVE_API", data: response.data || response };
      } catch (err) {
        const mockRes = await mockDataService.getFraudAlerts();
        return { source: "MOCK_FALLBACK", ...mockRes };
      }
    }
    const mockRes = await mockDataService.getFraudAlerts();
    return { source: "MOCK_MODE", ...mockRes };
  },

  // 9. Resolve Alert
  async resolveAlert(id, notes = "", mode = getStoredApiMode()) {
    if (mode === "LIVE") {
      try {
        const response = await apiClient.post(ENDPOINTS.RESOLVE_ALERT(id), { notes });
        return { source: "LIVE_API", ...response };
      } catch (err) {
        const mockRes = await mockDataService.resolveAlert(id, notes);
        return { source: "MOCK_FALLBACK", ...mockRes };
      }
    }
    const mockRes = await mockDataService.resolveAlert(id, notes);
    return { source: "MOCK_MODE", ...mockRes };
  }
};
