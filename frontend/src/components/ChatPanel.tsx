import { useChat } from "../hooks/useChat";
import { MessageList } from "./MessageList";
import { InputBox } from "./InputBox";
import { ErrorBanner } from "./ErrorBanner";

export function ChatPanel() {
  const { turns, isLoading, error, send, dismissError } = useChat();

  return (
    <div className="chat-panel">
      {error && <ErrorBanner message={error} onDismiss={dismissError} />}
      <MessageList turns={turns} isLoading={isLoading} />
      <InputBox onSend={send} disabled={isLoading} />
    </div>
  );
}
