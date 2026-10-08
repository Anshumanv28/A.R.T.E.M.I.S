import { useEffect, useState } from "react";
import { getCollectionDetail } from "../../api/client";
import type { CollectionDetailResponse } from "../../api/types";

interface Props {
  name: string;
}

function formatField(value: number | string | Record<string, number | string> | null): string {
  if (value === null) return "—";
  if (typeof value === "object") {
    return Object.entries(value)
      .map(([k, v]) => `${k}: ${v}`)
      .join(", ");
  }
  return String(value);
}

export function CollectionDetailCard({ name }: Props) {
  const [detail, setDetail] = useState<CollectionDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // On-demand fetch, independent of the collections list's poll cycle --
  // intentionally not part of usePolling, so expanding N rows never means
  // N extra Qdrant round-trips on every tick.
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getCollectionDetail(name)
      .then((data) => {
        if (cancelled) return;
        if (data.error) setError(data.error);
        else setDetail(data);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Request failed");
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [name]);

  if (loading) return <div className="collection-detail-card">Loading details…</div>;
  if (error || !detail) {
    return <div className="collection-detail-card collection-detail-error">{error ?? "Not found"}</div>;
  }

  return (
    <div className="collection-detail-card">
      <dl className="status-grid">
        <dt>Points</dt>
        <dd>{detail.points_count}</dd>
        <dt>Status</dt>
        <dd>{detail.status}</dd>
        <dt>Vector size</dt>
        <dd>{formatField(detail.vector_size)}</dd>
        <dt>Distance</dt>
        <dd>{formatField(detail.distance)}</dd>
        <dt>Segments</dt>
        <dd>{formatField(detail.segments_count)}</dd>
        <dt>Optimizer</dt>
        <dd>{formatField(detail.optimizer_status)}</dd>
      </dl>
    </div>
  );
}
