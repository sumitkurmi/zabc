import React, { useState } from 'react';
import { useChat } from '../../hooks/useChat';
import { useResizablePanel } from '../../hooks/useResizablePanel';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { ResizeHandle } from './ResizeHandle';
import {
  X,
  Minus,
  Sparkles,
  RotateCcw,
  Bot,
  AlertCircle
} from 'lucide-react';
import { ProblemType } from '../../types';

interface ChatPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onAutoFillForm: (data: { problem_type: ProblemType; additional_comment: string }) => void;
  hasAutoFilled: boolean;
}

const SUGGESTION_CHIPS = [
  'Wi-Fi keeps disconnecting',
  "Can't get an IP address",
  'Internet is very slow'
];

export const ChatPanel: React.FC<ChatPanelProps> = ({
  isOpen,
  onClose,
  onAutoFillForm,
  hasAutoFilled
}) => {
  const {
    messages,
    messageCount,
    detectedCategory,
    isLoading,
    error,
    limitReached,
    sendMessage,
    getSummary,
    startNewChat
  } = useChat();

  const { width, isResizing, startResizing, resetWidth } = useResizablePanel();
  const [isSummarizing, setIsSummarizing] = useState(false);

  if (!isOpen) return null;

  const userMessagesCount = messages.filter((m) => m.role === 'user').length;

  const handleLogRequestWithAI = async () => {
    try {
      setIsSummarizing(true);
      const summary = await getSummary();
      onAutoFillForm(summary);
    } catch (err: any) {
      alert(err.message || 'Failed to generate AI summary');
    } finally {
      setIsSummarizing(false);
    }
  };

  return (
    <div
      style={{ width: `${width}px` }}
      className="fixed top-0 right-0 h-full bg-slate-50 shadow-2xl z-50 flex flex-col border-l border-slate-200 transition-none w-full md:max-w-[80vw] min-w-[320px]"
    >
      {/* Resizable handle for desktop */}
      <ResizeHandle
        onMouseDown={startResizing}
        onDoubleClick={resetWidth}
        isResizing={isResizing}
      />

      {/* Header */}
      <div className="bg-mnnit-blue text-white p-3.5 flex items-center justify-between shrink-0 shadow-md">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center">
            <Bot className="w-5 h-5 text-mnnit-gold" />
          </div>
          <div>
            <h2 className="font-semibold text-sm">Network Assistant</h2>
            <p className="text-[11px] text-slate-300">
              {messageCount} / 10 messages
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-white/10 rounded-lg text-slate-300 hover:text-white transition-colors"
            title="Minimize chat"
          >
            <Minus className="w-4 h-4" />
          </button>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-white/10 rounded-lg text-slate-300 hover:text-white transition-colors"
            title="Close chat"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Privacy Notice Banner */}
      <div className="bg-blue-50 border-b border-blue-100 px-3.5 py-1.5 text-[11px] text-blue-800 flex items-center gap-1.5">
        <AlertCircle className="w-3.5 h-3.5 text-blue-600 shrink-0" />
        <span>Chats may be reviewed by the network team to improve support.</span>
      </div>

      {/* Suggestion Chips */}
      {messages.length <= 1 && (
        <div className="p-3 bg-white border-b border-slate-200">
          <p className="text-xs text-slate-500 mb-2 font-medium">Suggested queries:</p>
          <div className="flex flex-wrap gap-1.5">
            {SUGGESTION_CHIPS.map((chip, idx) => (
              <button
                key={idx}
                onClick={() => sendMessage(chip)}
                className="text-xs bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-700 px-2.5 py-1 rounded-full border border-slate-200 transition-colors"
              >
                {chip}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Message List */}
      <MessageList
        messages={messages}
        isLoading={isLoading}
        detectedCategory={detectedCategory}
      />

      {/* Limit Reached Banner */}
      {limitReached && (
        <div className="bg-amber-50 border-y border-amber-200 p-3 text-xs text-amber-800 flex flex-col gap-2">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <span>
              You've reached the 10-message limit. Click 'Log request using AI' to submit your complaint, or start a new chat.
            </span>
          </div>
          <button
            onClick={startNewChat}
            className="self-start text-xs bg-amber-600 hover:bg-amber-700 text-white font-medium px-3 py-1 rounded-lg flex items-center gap-1 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Start New Chat
          </button>
        </div>
      )}

      {/* Action area & "Log request using AI" button */}
      <div className="shrink-0 bg-white border-t border-slate-200 p-2.5 space-y-2">
        {userMessagesCount >= 1 && (
          <button
            onClick={handleLogRequestWithAI}
            disabled={isSummarizing}
            className="w-full py-2 px-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-medium text-xs rounded-xl shadow-sm flex items-center justify-center gap-1.5 transition-all disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4 text-mnnit-gold" />
            <span>
              {isSummarizing
                ? 'Summarizing transcript...'
                : hasAutoFilled
                ? 'Update form from chat'
                : 'Log request using AI'}
            </span>
          </button>
        )}

        <MessageInput onSend={sendMessage} disabled={limitReached || isLoading} />
      </div>
    </div>
  );
};
