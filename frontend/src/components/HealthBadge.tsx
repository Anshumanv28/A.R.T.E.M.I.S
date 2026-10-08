import { useEffect, useState } from "react";
import { getHealth } from "../api/client";

type Status = "checking" | "ok" | "unhealthy" | "unreachable";

export function HealthBadge() {
  const [status, setStatus] = useState<Status>("checking");
  const [reason, setReason] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getHealth()
      .then((res) => {
        if (cancelled) return;
        setStatus(res.status === "ok" ? "ok" : "unhealthy");
        setReason(res.reason ?? null);
      })
      .catch(() => {
        if (!cancelled) setStatus("unreachable");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const color =
    status === "ok"
      ? "var(--success)"
      : status === "checking"
        ? "var(--neutral)"
        : "var(--danger)";
  const label =
    status === "ok"
      ? "Backend ready"
      : status === "checking"
        ? "Checking backend…"
        : status === "unreachable"
          ? "Backend unreachable"
          : `Backend unhealthy${reason ? `: ${reason}` : ""}`;

  return (
    <div className="health-badge" title={label}>
      <span className="health-dot" style={{ backgroundColor: color }} />
      <span className="health-label">{label}</span>
    </div>
  );
}
