import { API_BASE_URL } from "../lib/env";
import type {
  QueryRequestBody,
  QueryResponse,
  HealthResponse,
  StatusResponse,
  CollectionsResponse,
  CollectionDetailResponse,
} from "./types";

export class ApiError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function postQuery(body: QueryRequestBody): Promise<QueryResponse> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiError("Could not reach the ARTEMIS API. Is the backend running?");
  }

  let data: QueryResponse;
  try {
    data = (await res.json()) as QueryResponse;
  } catch {
    throw new ApiError(`Request failed (${res.status})`, res.status);
  }

  // /query always returns a JSON body, including on 500/503, so use the
  // backend's own error string instead of a generic HTTP-status message.
  if (!res.ok) {
    throw new ApiError(data.error ?? `Request failed (${res.status})`, res.status);
  }
  return data;
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/health`);
  return (await res.json()) as HealthResponse;
}

// These three mirror getHealth(): the response body is self-describing even on
// 503/500 (e.g. {ready: false, reason: "..."}), so callers read the body's own
// fields rather than branching on res.ok. A thrown error here means the fetch
// itself failed (network/CORS), not an application-level problem.

export async function getStatus(): Promise<StatusResponse> {
  const res = await fetch(`${API_BASE_URL}/status`);
  return (await res.json()) as StatusResponse;
}

export async function getCollections(): Promise<CollectionsResponse> {
  const res = await fetch(`${API_BASE_URL}/collections`);
  return (await res.json()) as CollectionsResponse;
}

export async function getCollectionDetail(name: string): Promise<CollectionDetailResponse> {
  const res = await fetch(`${API_BASE_URL}/collections/${encodeURIComponent(name)}`);
  return (await res.json()) as CollectionDetailResponse;
}
