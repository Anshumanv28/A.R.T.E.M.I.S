import { useState } from "react";
import type { CollectionsResponse } from "../../api/types";
import { CollectionDetailCard } from "./CollectionDetailCard";

interface Props {
  data: CollectionsResponse | null;
  error: string | null;
  loading: boolean;
}

export function CollectionsList({ data, error, loading }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const collections = data?.collections ?? [];

  return (
    <div className="collections-list-card">
      <h2>Collections</h2>
      {loading && !data && <p className="status-loading">Loading…</p>}
      {(error || data?.error) && <p className="status-error">{error ?? data?.error}</p>}
      {data && collections.length === 0 && !error && !data.error && (
        <p className="collections-empty">No collections yet.</p>
      )}
      {collections.length > 0 && (
        <ul className="collections-list">
          {collections.map((c) => (
            <li key={c.name} className="collection-row">
              <button
                type="button"
                className="collection-row-toggle"
                onClick={() => setExpanded(expanded === c.name ? null : c.name)}
              >
                <span className="collection-name">{c.name}</span>
                {c.purpose && <span className="collection-purpose">{c.purpose}</span>}
              </button>
              {expanded === c.name && <CollectionDetailCard name={c.name} />}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
