import { useChat } from "../hooks/useChat";
import { MessageList } from "./MessageList";
import { InputBox } from "./InputBox";
import { ErrorBanner } from "./ErrorBanner";

export function ChatPanel() {
  const { turns, isLoading, error, send, dismissError, clearHistory } = useChat();

  return (
    <div className="chat-panel">
      {error && <ErrorBanner message={error} onDismiss={dismissError} />}
      <div className="chat-panel-toolbar">
        <button
          type="button"
          className="clear-chat-button"
          onClick={clearHistory}
          disabled={turns.length === 0 || isLoading}
        >
          Clear chat
        </button>
      </div>
      <MessageList turns={turns} isLoading={isLoading} />
      <InputBox onSend={send} disabled={isLoading} />
    </div>
  );
}
