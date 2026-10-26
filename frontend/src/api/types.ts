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

export interface EvalMetrics {
  total_cases: number;
  task_success_rate: number;
  routing_accuracy: number;
  tool_selection_accuracy: number;
  avg_step_count: number;
  avg_duration_s: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  total_cost_usd: number | null;
  pricing_unavailable_count: number;
  failure_breakdown: Record<string, number>;
}

export interface EvalCaseSummary {
  case_id: string;
  success: boolean;
  failure_reason: string | null;
  expected_agent: string;
  actual_agent: string | null;
  duration_s: number;
}

export interface EvalLatestResponse {
  report_file: string | null;
  generated_at: string | null;
  metrics: EvalMetrics | null;
  cases: EvalCaseSummary[];
  error?: string;
}
