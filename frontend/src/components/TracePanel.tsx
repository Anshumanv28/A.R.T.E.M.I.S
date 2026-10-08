import type { ToolCall } from "../api/types";

interface Props {
  routedTo?: string | null;
  toolCalls?: ToolCall[] | null;
}

export function TracePanel({ routedTo, toolCalls }: Props) {
  return (
    <details className="trace-panel">
      <summary>View trace{routedTo ? ` — routed to ${routedTo}` : ""}</summary>
      <div className="trace-body">
        <div>
          <strong>Routed to:</strong> {routedTo ?? "unknown"}
        </div>
        <div>
          <strong>Tool calls:</strong>
          {toolCalls && toolCalls.length > 0 ? (
            <pre>{JSON.stringify(toolCalls, null, 2)}</pre>
          ) : (
            <span> none</span>
          )}
        </div>
      </div>
    </details>
  );
}
