import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import { AgentsPage } from "./pages/AgentsPage";
import { AlertsPage } from "./pages/AlertsPage";
import { CostsPage } from "./pages/CostsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LLMRuntimePage } from "./pages/LLMRuntimePage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 2, staleTime: 20_000, refetchOnWindowFocus: false },
  },
});

export const App: React.FC = () => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="agents" element={<AgentsPage />} />
          <Route path="costs" element={<CostsPage />} />
          <Route path="alerts" element={<AlertsPage />} />
          <Route path="llm" element={<LLMRuntimePage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </QueryClientProvider>
);
