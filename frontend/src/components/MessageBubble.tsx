import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
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
      {isAssistant ? (
        <div className="message-content markdown">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{turn.content}</ReactMarkdown>
        </div>
      ) : (
        <div className="message-content">{turn.content}</div>
      )}
      {isAssistant && hasTrace && (
        <TracePanel routedTo={turn.routedTo} toolCalls={turn.toolCalls} />
      )}
    </div>
  );
}
