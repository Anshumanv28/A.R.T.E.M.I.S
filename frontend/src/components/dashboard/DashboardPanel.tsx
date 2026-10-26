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

  return (
    <div className="dashboard-panel">
      <div className="dashboard-toolbar">
        <button type="button" className="dashboard-refresh-button" onClick={refreshAll}>
          Refresh
        </button>
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
