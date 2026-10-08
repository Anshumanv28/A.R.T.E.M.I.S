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
