// Centralized FastAPI Backend Endpoints definition

export const ENDPOINTS = {
  HEALTH: "/api/v1/health",
  ANALYZE_TRANSACTION: "/api/v1/fraud/analyze",
  TRANSACTIONS: "/api/v1/transactions",
  TRANSACTION_DETAIL: (id) => `/api/v1/transactions/${id}`,
  COLLECT_REQUESTS: "/api/v1/collect-requests",
  COLLECT_REQUEST_ACTION: (id) => `/api/v1/collect-requests/${id}/action`,
  FRAUD_ANALYTICS: "/api/v1/fraud/analytics",
  SCREENSHOT_SCAN: "/api/v1/fraud/screenshot-ocr",
  FRAUD_ALERTS: "/api/v1/fraud/alerts",
  RESOLVE_ALERT: (id) => `/api/v1/fraud/alerts/${id}/resolve`
};
