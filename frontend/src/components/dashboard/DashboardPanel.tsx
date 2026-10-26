import { getStatus, getCollections, getEvalLatest } from "../../api/client";
import { usePolling } from "../../hooks/usePolling";
import { StatusCard } from "./StatusCard";
import { CollectionsList } from "./CollectionsList";
import { EvalCard } from "./EvalCard";

export function DashboardPanel() {
  // Independent poll instances -- a slow collections fetch should never
  // block the status badge from updating.
  const status = usePolling(getStatus);
  const collections = usePolling(getCollections);
  const evalLatest = usePolling(getEvalLatest);

  const refreshAll = () => {
    status.refresh();
    collections.refresh();
    evalLatest.refresh();
  };

  const ready = status.data?.ready ?? false;
  const collectionsCount = collections.data?.collections.length ?? null;
  const successRate = evalLatest.data?.metrics?.task_success_rate ?? null;

  return (
    <div className="dashboard-panel">
      <div className="dashboard-toolbar">
        <button type="button" className="dashboard-refresh-button" onClick={refreshAll}>
          Refresh
        </button>
      </div>
      <div className="stat-strip">
        <div className="stat-tile">
          <span className="stat-tile-label">Backend</span>
          <span className="stat-tile-value">
            <span
              className="status-dot"
              style={{ backgroundColor: ready ? "var(--success)" : "var(--danger)" }}
            />
            {status.loading && !status.data ? "Checking…" : ready ? "Online" : "Offline"}
          </span>
        </div>
        <div className="stat-tile">
          <span className="stat-tile-label">Collections</span>
          <span className="stat-tile-value">{collectionsCount ?? "—"}</span>
        </div>
        <div className="stat-tile">
          <span className="stat-tile-label">Latest eval success</span>
          <span className="stat-tile-value">
            {successRate != null ? `${Math.round(successRate * 100)}%` : "—"}
          </span>
        </div>
      </div>
      <div className="dashboard-grid">
        <StatusCard data={status.data} error={status.error} loading={status.loading} />
        <CollectionsList
          data={collections.data}
          error={collections.error}
          loading={collections.loading}
        />
        <EvalCard data={evalLatest.data} error={evalLatest.error} loading={evalLatest.loading} />
      </div>
    </div>
  );
}
