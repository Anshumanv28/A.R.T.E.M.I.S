import { useState } from "react";
import type { ToolCall } from "../api/types";

interface Props {
  routedTo?: string | null;
  toolCalls?: ToolCall[] | null;
}

function toolName(call: ToolCall): string {
  const name = call["tool_name"] ?? call["name"];
  return typeof name === "string" ? name : "tool";
}

function toolOk(call: ToolCall): boolean {
  return call["ok"] !== false;
}

export function TracePanel({ routedTo, toolCalls }: Props) {
  const [open, setOpen] = useState(false);
  const calls = toolCalls ?? [];

  return (
    <div className="trace-panel">
      <div className="trace-summary-row">
        {routedTo && <span className="trace-chip">{routedTo}</span>}
        <button type="button" className="trace-toggle" onClick={() => setOpen((v) => !v)}>
          {open ? "Hide trace" : `View trace${calls.length ? ` (${calls.length} tool call${calls.length === 1 ? "" : "s"})` : ""}`}
        </button>
      </div>
      {open && (
        <div className="trace-body">
          <p className="trace-body-label">Tool calls</p>
          {calls.length > 0 ? (
            <ul className="trace-tool-list">
              {calls.map((call, i) => (
                <li key={i} className="trace-tool-row">
                  <span className={`trace-tool-status ${toolOk(call) ? "ok" : "error"}`}>
                    {toolOk(call) ? "ok" : "err"}
                  </span>
                  <span className="trace-tool-name">{toolName(call)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="trace-body-label" style={{ textTransform: "none", letterSpacing: 0 }}>
              No tools called — answered directly.
            </p>
          )}
          {calls.length > 0 && <pre>{JSON.stringify(calls, null, 2)}</pre>}
        </div>
      )}
    </div>
  );
}
