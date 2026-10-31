import axios from "axios";

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 8000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json"
  }
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Inject headers or auth tokens if available
    config.headers["X-Client-Platform"] = "UPI-Shield-Web";
    config.headers["X-Request-Time"] = new Date().toISOString();
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for consistent error normalization
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const errorPayload = {
      isApiError: true,
      status: error.response?.status || 0,
      message: error.response?.data?.error?.message || error.response?.data?.detail || error.response?.data?.message || error.message || "Network error. Backend unreachable.",
      code: error.code,
      data: error.response?.data || null
    };
    return Promise.reject(errorPayload);
  }
);

export default apiClient;
