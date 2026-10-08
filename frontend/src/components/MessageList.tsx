import { useEffect, useRef } from "react";
import type { ChatTurn } from "../hooks/useChat";
import { MessageBubble } from "./MessageBubble";
import { LoadingIndicator } from "./LoadingIndicator";

interface Props {
  turns: ChatTurn[];
  isLoading: boolean;
}

export function MessageList({ turns, isLoading }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns.length, isLoading]);

  return (
    <div className="message-list">
      {turns.length === 0 && !isLoading && (
        <div className="empty-state">
          Ask A.R.T.E.M.I.S something — it'll route your question to the right agent (search,
          ingestion, or collection management) and show its reasoning trace below the answer.
        </div>
      )}
      {turns.map((turn) => (
        <MessageBubble key={turn.id} turn={turn} />
      ))}
      {isLoading && <LoadingIndicator />}
      <div ref={bottomRef} />
    </div>
  );
}
