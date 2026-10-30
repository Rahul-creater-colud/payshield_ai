import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { getStoredApiMode, setStoredApiMode, apiService } from "../services/apiService";

const ApiModeContext = createContext(null);

export const ApiModeProvider = ({ children }) => {
  const [mode, setMode] = useState(getStoredApiMode);
  const [isBackendReachable, setIsBackendReachable] = useState(false);
  const [isCheckingBackend, setIsCheckingBackend] = useState(false);
  const [lastCheckTime, setLastCheckTime] = useState(null);

  const checkConnectivity = useCallback(async () => {
    setIsCheckingBackend(true);
    const res = await apiService.pingBackend();
    setIsBackendReachable(res.connected);
    setLastCheckTime(new Date());
    setIsCheckingBackend(false);
    return res.connected;
  }, []);

  useEffect(() => {
    // Initial check on mount
    checkConnectivity();
    // Periodic check every 15 seconds
    const interval = setInterval(checkConnectivity, 15000);
    return () => clearInterval(interval);
  }, [checkConnectivity]);

  const toggleMode = (newMode) => {
    const targetMode = newMode || (mode === "MOCK" ? "LIVE" : "MOCK");
    setMode(targetMode);
    setStoredApiMode(targetMode);
    if (targetMode === "LIVE") {
      checkConnectivity();
    }
  };

  return (
    <ApiModeContext.Provider
      value={{
        mode,
        isLiveMode: mode === "LIVE",
        isMockMode: mode === "MOCK",
        toggleMode,
        isBackendReachable,
        isCheckingBackend,
        lastCheckTime,
        checkConnectivity
      }}
    >
      {children}
    </ApiModeContext.Provider>
  );
};

export const useApiMode = () => {
  const context = useContext(ApiModeContext);
  if (!context) {
    throw new Error("useApiMode must be used within an ApiModeProvider");
  }
  return context;
};
