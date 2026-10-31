import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ApiModeProvider } from "./hooks/useApiMode";
import { ToastProvider } from "./hooks/useToast";
import MainLayout from "./layouts/MainLayout";

import Dashboard from "./pages/Dashboard";
import TransactionAnalysis from "./pages/TransactionAnalysis";
import CollectRequestWarning from "./pages/CollectRequestWarning";
import FraudAnalytics from "./pages/FraudAnalytics";
import TransactionHistory from "./pages/TransactionHistory";
import ScreenshotPanel from "./pages/ScreenshotPanel";
import AlertsRiskReport from "./pages/AlertsRiskReport";
import MerchantVerification from "./pages/MerchantVerification";
import FraudNetwork from "./pages/FraudNetwork";
import IntelligenceGrievance from "./pages/IntelligenceGrievance";
import SuspiciousUrlScanner from "./pages/SuspiciousUrlScanner";
import NotFound from "./pages/NotFound";

export const App = () => {
  return (
    <ApiModeProvider>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<MainLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="analyze" element={<TransactionAnalysis />} />
              <Route path="collect-requests" element={<CollectRequestWarning />} />
              <Route path="analytics" element={<FraudAnalytics />} />
              <Route path="fraud-network" element={<FraudNetwork />} />
              <Route path="merchant-verification" element={<MerchantVerification />} />
              <Route path="intelligence" element={<IntelligenceGrievance />} />
              <Route path="url-scanner" element={<SuspiciousUrlScanner />} />
              <Route path="history" element={<TransactionHistory />} />
              <Route path="screenshot-scanner" element={<ScreenshotPanel />} />
              <Route path="alerts-report" element={<AlertsRiskReport />} />
              <Route path="*" element={<NotFound />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </ApiModeProvider>
  );
};

export default App;
