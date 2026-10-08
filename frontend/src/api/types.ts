export type Role = "user" | "assistant";

export interface HistoryMessage {
  role: Role;
  content: string;
}

export interface QueryRequestBody {
  query: string;
  message_history?: HistoryMessage[] | null;
}

// The backend doesn't pin down a strict shape for individual tool_calls
// entries, so treat them generically and render defensively (JSON/list),
// not via assumed typed fields.
export type ToolCall = Record<string, unknown>;

export interface QueryResponse {
  final_answer: string | null;
  routed_to: string | null;
  error: string | null;
  tool_calls: ToolCall[] | null;
}

export interface HealthResponse {
  status: "ok" | "unhealthy";
  reason?: string;
}

export interface StatusResponse {
  ready: boolean;
  reason: string | null;
  provider: "groq" | "openai" | null;
  model_name: string | null;
  qdrant_reachable: boolean;
  qdrant_error: string | null;
}

export interface CollectionSummary {
  name: string;
  purpose: string | null;
}

export interface CollectionsResponse {
  collections: CollectionSummary[];
  error?: string;
}

export interface CollectionDetailResponse {
  name: string;
  points_count: number;
  vectors_count: number;
  status: string;
  vector_size: number | Record<string, number>;
  distance: string | Record<string, string>;
  segments_count: number | null;
  optimizer_status: string | null;
  error?: string;
}
