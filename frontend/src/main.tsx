import React from "react";
import ReactDOM from "react-dom/client";
import "./telemetry";
import { App } from "./App";
import { ThemeProvider } from "./components/ThemeContext";
import { ToastProvider } from "./components/ToastContext";
import { registerServiceWorker } from "./pwa";
import "./styles/global.css";

registerServiceWorker();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider>
      <ToastProvider>
        <App />
      </ToastProvider>
    </ThemeProvider>
  </React.StrictMode>
);
