import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { ToastContainer } from "./components/ToastContainer";
import { AgentsPage } from "./pages/AgentsPage";
import { AlertsPage } from "./pages/AlertsPage";
import { CostsPage } from "./pages/CostsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LLMRuntimePage } from "./pages/LLMRuntimePage";
import { ModelPage } from "./pages/ModelPage";
import { SettingsPage } from "./pages/SettingsPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 2, staleTime: 20_000, refetchOnWindowFocus: false },
  },
});

export const App: React.FC = () => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      <ErrorBoundary>
        <ToastContainer />
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="agents" element={<AgentsPage />} />
            <Route path="costs" element={<CostsPage />} />
            <Route path="alerts" element={<AlertsPage />} />
            <Route path="llm" element={<LLMRuntimePage />} />
            <Route path="models/:modelName" element={<ModelPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </ErrorBoundary>
    </BrowserRouter>
  </QueryClientProvider>
);
