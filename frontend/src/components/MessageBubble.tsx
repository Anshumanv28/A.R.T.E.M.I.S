import type { ChatTurn } from "../hooks/useChat";
import { TracePanel } from "./TracePanel";

interface Props {
  turn: ChatTurn;
}

export function MessageBubble({ turn }: Props) {
  const isAssistant = turn.role === "assistant";
  const hasTrace = turn.routedTo !== undefined || turn.toolCalls !== undefined;

  return (
    <div className={`message-bubble ${turn.role}`}>
      <div className="message-content">{turn.content}</div>
      {isAssistant && hasTrace && (
        <TracePanel routedTo={turn.routedTo} toolCalls={turn.toolCalls} />
      )}
    </div>
  );
}
