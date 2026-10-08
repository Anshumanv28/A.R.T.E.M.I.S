import type { StatusResponse } from "../../api/types";

interface Props {
  data: StatusResponse | null;
  error: string | null;
  loading: boolean;
}

export function StatusCard({ data, error, loading }: Props) {
  const ready = data?.ready ?? false;
  const qdrantReachable = data?.qdrant_reachable ?? false;

  return (
    <div className="status-card">
      <h2>System status</h2>
      {loading && !data && <p className="status-loading">Checking…</p>}
      {error && !data && <p className="status-error">{error}</p>}
      {data && (
        <dl className="status-grid">
          <dt>Backend</dt>
          <dd>
            <span
              className="status-dot"
              style={{ backgroundColor: ready ? "var(--success)" : "var(--danger)" }}
            />
            {ready ? "Online" : (data.reason ?? "Offline")}
          </dd>

          <dt>Qdrant</dt>
          <dd>
            <span
              className="status-dot"
              style={{ backgroundColor: qdrantReachable ? "var(--success)" : "var(--danger)" }}
            />
            {qdrantReachable ? "Reachable" : (data.qdrant_error ?? "Unreachable")}
          </dd>

          <dt>Provider</dt>
          <dd>{data.provider ?? "—"}</dd>

          <dt>Model</dt>
          <dd>{data.model_name ?? "—"}</dd>
        </dl>
      )}
    </div>
  );
}
