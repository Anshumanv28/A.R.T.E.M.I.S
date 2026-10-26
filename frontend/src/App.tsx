import { useState } from "react";
import { ChatPanel } from "./components/ChatPanel";
import { HealthBadge } from "./components/HealthBadge";
import { ThemeToggle } from "./components/ThemeToggle";
import { DashboardPanel } from "./components/dashboard/DashboardPanel";

export default function App() {
  const [tab, setTab] = useState<"chat" | "dashboard">("chat");

  return (
    <div className={`app ${tab === "dashboard" ? "app--wide" : ""}`}>
      <header className="app-header">
        <div className="app-brand">
          <h1>A.R.T.E.M.I.S</h1>
          <span className="app-tagline">Supervisor-routed multi-agent RAG</span>
        </div>
        <nav className="tab-switch">
          <button
            type="button"
            className={tab === "chat" ? "active" : ""}
            onClick={() => setTab("chat")}
          >
            Chat
          </button>
          <button
            type="button"
            className={tab === "dashboard" ? "active" : ""}
            onClick={() => setTab("dashboard")}
          >
            Dashboard
          </button>
        </nav>
        <div className="header-controls">
          <HealthBadge />
          <ThemeToggle />
        </div>
      </header>
      <main>{tab === "chat" ? <ChatPanel /> : <DashboardPanel />}</main>
    </div>
  );
}
