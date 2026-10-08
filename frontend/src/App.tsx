import { ChatPanel } from "./components/ChatPanel";
import { HealthBadge } from "./components/HealthBadge";
import { ThemeToggle } from "./components/ThemeToggle";

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>A.R.T.E.M.I.S</h1>
        <div className="header-controls">
          <HealthBadge />
          <ThemeToggle />
        </div>
      </header>
      <main>
        <ChatPanel />
      </main>
    </div>
  );
}
