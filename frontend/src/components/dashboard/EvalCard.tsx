import type { EvalLatestResponse } from "../../api/types";

interface Props {
  data: EvalLatestResponse | null;
  error: string | null;
  loading: boolean;
}

function formatPct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function EvalCard({ data, error, loading }: Props) {
  const metrics = data?.metrics ?? null;
  const cases = data?.cases ?? [];

  return (
    <div className="eval-card">
      <h2>Agent eval (latest run)</h2>
      {loading && !data && <p className="status-loading">Loading…</p>}
      {error && <p className="status-error">{error}</p>}
      {/* A 404 "no reports yet" is a normal first-run state, not a server error -- the
          backend reports it via data.error (self-describing body) rather than a thrown
          fetch error, so it gets a plain empty state instead of the red error banner. */}
      {!error && data && !metrics && (
        <p className="eval-empty">
          No eval run yet. Run{" "}
          <code>python scripts/eval_agent.py --dataset tests/eval/golden_dataset.json --skip-mutating</code>{" "}
          to generate one.
        </p>
      )}
      {metrics && (
        <>
          <div className="eval-score-row">
            <span className="eval-score-value">{formatPct(metrics.task_success_rate)}</span>
            <span className="eval-score-fraction">
              {cases.filter((c) => c.success).length}/{metrics.total_cases} cases passed
            </span>
          </div>
          <div className="eval-bar-track">
            <div
              className={`eval-bar-fill ${
                metrics.task_success_rate >= 0.8
                  ? ""
                  : metrics.task_success_rate >= 0.5
                    ? "degraded"
                    : "poor"
              }`}
              style={{ width: `${Math.round(metrics.task_success_rate * 100)}%` }}
            />
          </div>
          <dl className="status-grid">
            <dt>Routing accuracy</dt>
            <dd>{formatPct(metrics.routing_accuracy)}</dd>
            <dt>Tool-selection accuracy</dt>
            <dd>{formatPct(metrics.tool_selection_accuracy)}</dd>
            <dt>Avg steps</dt>
            <dd>{metrics.avg_step_count.toFixed(1)}</dd>
            <dt>Tokens</dt>
            <dd>{metrics.total_tokens.toLocaleString()}</dd>
            <dt>Cost</dt>
            <dd>
              {metrics.total_cost_usd != null
                ? `$${metrics.total_cost_usd.toFixed(6)}`
                : "pricing unavailable"}
            </dd>
          </dl>

          {Object.keys(metrics.failure_breakdown).length > 0 && (
            <ul className="eval-failure-breakdown">
              {Object.entries(metrics.failure_breakdown).map(([reason, count]) => (
                <li key={reason}>
                  {reason}: {count}
                </li>
              ))}
            </ul>
          )}

          <ul className="eval-case-list">
            {cases.map((c) => (
              <li key={c.case_id} className="eval-case-row">
                <span
                  className="status-dot"
                  style={{ backgroundColor: c.success ? "var(--success)" : "var(--danger)" }}
                />
                <span className="eval-case-id">{c.case_id}</span>
                {!c.success && c.failure_reason && (
                  <span className="eval-case-reason">({c.failure_reason})</span>
                )}
              </li>
            ))}
          </ul>

          {data?.generated_at && (
            <p className="eval-report-meta">
              Report: {data.report_file} ({data.generated_at})
            </p>
          )}
        </>
      )}
    </div>
  );
}
