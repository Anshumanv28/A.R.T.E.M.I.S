import { useCallback, useState } from "react";
import { postQuery, ApiError } from "../api/client";
import type { HistoryMessage, ToolCall } from "../api/types";

export interface ChatTurn {
  id: string;
  role: "user" | "assistant";
  content: string;
  routedTo?: string | null;
  toolCalls?: ToolCall[] | null;
}

interface ChatState {
  turns: ChatTurn[];
  isLoading: boolean;
  error: string | null;
}

function makeId(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2);
}

export function useChat() {
  const [state, setState] = useState<ChatState>({
    turns: [],
    isLoading: false,
    error: null,
  });

  const send = useCallback(async (query: string) => {
    const trimmed = query.trim();
    if (!trimmed) return;

    const userTurn: ChatTurn = { id: makeId(), role: "user", content: trimmed };

    // Snapshot history (pre-this-turn) from current state, then optimistically
    // append the user turn. The backend holds no session state, so every
    // request must resend the full prior conversation.
    let history: HistoryMessage[] = [];
    setState((prev) => {
      history = prev.turns.map((t) => ({ role: t.role, content: t.content }));
      return { turns: [...prev.turns, userTurn], isLoading: true, error: null };
    });

    try {
      const result = await postQuery({ query: trimmed, message_history: history });
      const assistantTurn: ChatTurn = {
        id: makeId(),
        role: "assistant",
        content: result.final_answer ?? "(no answer returned)",
        routedTo: result.routed_to,
        toolCalls: result.tool_calls,
      };
      setState((prev) => ({
        turns: [...prev.turns, assistantTurn],
        isLoading: false,
        error: null,
      }));
    } catch (err) {
      // Don't fabricate an assistant turn on failure — keep turns consistent
      // with what the backend actually produced, since turns are resent as
      // message_history on the next call.
      const message = err instanceof ApiError ? err.message : "Unexpected error";
      setState((prev) => ({ ...prev, isLoading: false, error: message }));
    }
  }, []);

  const dismissError = useCallback(() => {
    setState((prev) => ({ ...prev, error: null }));
  }, []);

  return {
    turns: state.turns,
    isLoading: state.isLoading,
    error: state.error,
    send,
    dismissError,
  };
}
