import React, { useEffect, useRef } from 'react';
import { ChatTurn, ProblemType } from '../../types';
import { Bot, User, AlertCircle } from 'lucide-react';
import { MarkdownMessage } from './MarkdownMessage';

interface MessageListProps {
  messages: ChatTurn[];
  isLoading: boolean;
  detectedCategory: ProblemType | null;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  isLoading,
  detectedCategory,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((msg, index) => {
        const isUser = msg.role === 'user';
        return (
          <div
            key={index}
            className={`flex items-start gap-2.5 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-white font-medium ${
                isUser ? 'bg-blue-600' : 'bg-slate-700'
              }`}
            >
              {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            <div
              className={`max-w-[85%] rounded-2xl p-3.5 text-sm shadow-sm overflow-hidden ${
                isUser
                  ? 'bg-blue-600 text-white rounded-tr-none'
                  : 'bg-white border border-slate-200 text-slate-800 rounded-tl-none'
              }`}
            >
              {isUser ? (
                <div className="whitespace-pre-wrap leading-relaxed text-xs">{msg.content}</div>
              ) : (
                <MarkdownMessage content={msg.content} />
              )}

              {/* Detected category chip on assistant reply */}
              {!isUser && detectedCategory && index === messages.length - 1 && (
                <div className="mt-2.5 inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                  <span>Detected: {detectedCategory.replace(/_/g, ' ')}</span>
                </div>
              )}

              {/* Off-topic notice chip */}
              {msg.is_off_topic && (
                <div className="mt-2 flex items-center gap-1 text-xs text-amber-600 font-medium">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>Off-topic question</span>
                </div>
              )}
            </div>
          </div>
        );
      })}

      {isLoading && (
        <div className="flex items-start gap-2.5">
          <div className="w-8 h-8 rounded-full bg-slate-700 text-white flex items-center justify-center shrink-0">
            <Bot className="w-4 h-4" />
          </div>
          <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none p-4 shadow-sm">
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-blue-600 animate-bounce" />
              <div className="w-2 h-2 rounded-full bg-blue-600 animate-bounce [animation-delay:0.2s]" />
              <div className="w-2 h-2 rounded-full bg-blue-600 animate-bounce [animation-delay:0.4s]" />
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};
