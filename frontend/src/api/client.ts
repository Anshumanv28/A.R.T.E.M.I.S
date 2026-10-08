import { API_BASE_URL } from "../lib/env";
import type { QueryRequestBody, QueryResponse, HealthResponse } from "./types";

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
