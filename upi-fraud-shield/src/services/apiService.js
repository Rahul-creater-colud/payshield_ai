import apiClient from "../api/axiosClient";
import { ENDPOINTS } from "../api/endpoints";
import { mockDataService } from "./mockDataService";

export const getStoredApiMode = () => {
  const saved = localStorage.getItem("UPI_SHIELD_API_MODE");
  return saved || "LIVE";
};

export const setStoredApiMode = (mode) => {
  localStorage.setItem("UPI_SHIELD_API_MODE", mode);
};

const requireLiveMode = (mode) => {
  if (mode !== "LIVE") {
    throw new Error("Switch to LOCAL API mode to access persisted backend records.");
  }
};

export const apiService = {
  async pingBackend() {
    try {
      const data = await apiClient.get(ENDPOINTS.HEALTH);
      return { connected: data.db !== "error", data };
    } catch (err) {
      return { connected: false, error: err.message || "Failed to connect to FastAPI backend" };
    }
  },

  async analyzeTransaction(formData, mode = getStoredApiMode()) {
    if (mode === "LIVE") {
      const response = await apiClient.post(ENDPOINTS.ANALYZE_TRANSACTION, {
        transaction_id: formData.transactionId,
        sender_upi: formData.senderUpi,
        receiver_upi: formData.receiverUpi,
        amount: parseFloat(formData.amount),
        transaction_time: formData.transactionTime || new Date().toISOString(),
        transaction_type: formData.transactionType
      });
      return { source: "LIVE_API", data: response.data || response };
    }
    const result = await mockDataService.analyzeTransaction(formData);
    return { source: "MOCK_MODE", data: result.data };
  },

  async getTransactions(params = {}, mode = getStoredApiMode()) {
    if (mode === "LIVE") {
      const response = await apiClient.get(ENDPOINTS.TRANSACTIONS, { params });
      return { source: "LIVE_API", data: response.data || response, total: response.total };
    }
    const result = await mockDataService.getTransactions(params);
    return { source: "MOCK_MODE", data: result.data, total: result.total };
  },

  async getTransactionDetail(id, mode = getStoredApiMode()) {
    if (mode === "LIVE") {
      const response = await apiClient.get(ENDPOINTS.TRANSACTION_DETAIL(id));
      return { source: "LIVE_API", data: response.data || response };
    }
    const result = await mockDataService.getTransactionDetail(id);
    return { source: "MOCK_MODE", data: result.data };
  },

  async getCollectRequests(mode = getStoredApiMode()) {
    if (mode === "LIVE") {
      const response = await apiClient.get(ENDPOINTS.COLLECT_REQUESTS);
      return { source: "LIVE_API", data: response.data || response, total: response.total };
    }
    const result = await mockDataService.getCollectRequests();
    return { source: "MOCK_MODE", data: result.data, total: result.total };
  },

  async actionCollectRequest(id, action, mode = getStoredApiMode()) {
    if (mode === "LIVE") {
      const response = await apiClient.post(ENDPOINTS.COLLECT_REQUEST_ACTION(id), { action });
      return { source: "LIVE_API", ...response };
    }
    const result = await mockDataService.actionCollectRequest(id, action);
    return { source: "MOCK_MODE", ...result };
  },

  async getFraudAnalytics(filters = {}, mode = getStoredApiMode()) {
    if (mode === "LIVE") {
      const response = await apiClient.get(ENDPOINTS.FRAUD_ANALYTICS, { params: filters });
      return { source: "LIVE_API", data: response };
    }
    const result = await mockDataService.getFraudAnalytics(filters);
    return { source: "MOCK_MODE", ...result };
  },

  async scanScreenshot(file, sampleKey = null, mode = getStoredApiMode()) {
    if (mode === "LIVE") {
      const formData = new FormData();
      if (file) formData.append("image", file);
      if (sampleKey) formData.append("sample_key", sampleKey);

      const response = await apiClient.post(ENDPOINTS.SCREENSHOT_SCAN, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      return {
        source: "LIVE_API",
        data: {
          ...response.data,
          data_label: response.data_label,
          simulated: response.simulated
        }
      };
    }
    const result = await mockDataService.scanScreenshot(file, sampleKey);
    return { source: "MOCK_MODE", ...result };
  },

  async getFraudAlerts(mode = getStoredApiMode()) {
    if (mode === "LIVE") {
      const response = await apiClient.get(ENDPOINTS.FRAUD_ALERTS);
      return { source: "LIVE_API", data: response };
    }
    const result = await mockDataService.getFraudAlerts();
    return { source: "MOCK_MODE", ...result };
  },

  async resolveAlert(id, notes = "", mode = getStoredApiMode()) {
    if (mode === "LIVE") {
      const response = await apiClient.post(ENDPOINTS.RESOLVE_ALERT(id), { notes });
      return { source: "LIVE_API", ...response };
    }
    const result = await mockDataService.resolveAlert(id, notes);
    return { source: "MOCK_MODE", ...result };
  },

  async getCatalog(mode = getStoredApiMode()) {
    requireLiveMode(mode);
    return { source: "LIVE_API", data: await apiClient.get(ENDPOINTS.CATALOG) };
  },

  async getAccountNetwork(accountId, depth = 2, mode = getStoredApiMode()) {
    requireLiveMode(mode);
    const data = await apiClient.get(ENDPOINTS.ACCOUNT_NETWORK(accountId), { params: { depth } });
    return { source: "LIVE_API", data };
  },

  async getIntelligence(params = {}, mode = getStoredApiMode()) {
    requireLiveMode(mode);
    return { source: "LIVE_API", data: await apiClient.get(ENDPOINTS.INTELLIGENCE, { params }) };
  },

  async reportIntelligence(payload, mode = getStoredApiMode()) {
    requireLiveMode(mode);
    return { source: "LIVE_API", data: await apiClient.post(ENDPOINTS.REPORT_INTELLIGENCE, payload) };
  },

  async updateIntelligence(id, payload, mode = getStoredApiMode()) {
    requireLiveMode(mode);
    return { source: "LIVE_API", data: await apiClient.patch(`${ENDPOINTS.INTELLIGENCE}/${encodeURIComponent(id)}`, payload) };
  },

  async getGrievances(params = {}, mode = getStoredApiMode()) {
    requireLiveMode(mode);
    return { source: "LIVE_API", data: await apiClient.get(ENDPOINTS.GRIEVANCES, { params }) };
  },

  async createGrievance(payload, mode = getStoredApiMode()) {
    requireLiveMode(mode);
    return { source: "LIVE_API", data: await apiClient.post(ENDPOINTS.GRIEVANCES, payload) };
  },

  async updateGrievance(id, payload, mode = getStoredApiMode()) {
    requireLiveMode(mode);
    return { source: "LIVE_API", data: await apiClient.patch(ENDPOINTS.GRIEVANCE(id), payload) };
  },

  async getRiskAssessments(params = {}, mode = getStoredApiMode()) {
    requireLiveMode(mode);
    return { source: "LIVE_API", data: await apiClient.get(ENDPOINTS.RISK_ASSESSMENTS, { params }) };
  },

  async scanUrl(url, mode = getStoredApiMode()) {
    requireLiveMode(mode);
    return { source: "LIVE_API", data: await apiClient.post(ENDPOINTS.URL_SCAN, { url }) };
  }
};
