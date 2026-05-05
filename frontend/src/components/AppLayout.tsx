import React from "react";
import { NavLink, Outlet } from "react-router-dom";

const links = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/agents", label: "Agents" },
  { to: "/costs", label: "Costs" },
  { to: "/alerts", label: "Alerts" },
  { to: "/llm", label: "LLM Runtime" },
];

export const AppLayout: React.FC = () => (
  <div className="app-shell">
    <aside className="sidebar">
      <h1>
        <span className="dot" /> Vectaris
      </h1>
      <nav>
        {links.map((l) => (
          <NavLink key={l.to} to={l.to} end={l.end}>
            {l.label}
          </NavLink>
        ))}
      </nav>
      <div className="footer">v1.0.0 · AI Platform Observability</div>
    </aside>
    <main className="content">
      <Outlet />
    </main>
  </div>
);
