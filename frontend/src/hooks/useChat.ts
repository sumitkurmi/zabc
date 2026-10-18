import { useState, useEffect, useCallback } from 'react';
import { createChat, sendChatMessage, summarizeChat, getChatTranscript } from '../api/chat';
import { ChatTurn, ProblemType } from '../types';

/**
 * Custom hook for student chatbot conversation state management.
 * Section 5.4.
 */
export function useChat() {
  const [chatId, setChatId] = useState<string | null>(() => sessionStorage.getItem('student_chat_id'));
  const [messages, setMessages] = useState<ChatTurn[]>([]);
  const [messageCount, setMessageCount] = useState<number>(0);
  const [detectedCategory, setDetectedCategory] = useState<ProblemType | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [limitReached, setLimitReached] = useState<boolean>(false);

  // Initialize fresh chat session if none exists
  const initChat = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await createChat();
      setChatId(res.chat_id);
      sessionStorage.setItem('student_chat_id', res.chat_id);
      setMessages([
        {
          role: 'assistant',
          content: 'Hello! I am the MNNIT Network Assistant. How can I help you with your campus network connection today?',
          created_at: new Date().toISOString()
        }
      ]);
      setMessageCount(0);
      setDetectedCategory(null);
      setLimitReached(false);
    } catch (err: any) {
      setError(err.message || 'Failed to initialize chat session');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Restore chat state on reload if chat_id exists in sessionStorage
  useEffect(() => {
    if (chatId) {
      getChatTranscript(chatId)
        .then((data) => {
          if (data.messages && data.messages.length > 0) {
            setMessages(data.messages);
          } else {
            setMessages([
              {
                role: 'assistant',
                content: 'Hello! I am the MNNIT Network Assistant. How can I help you with your campus network connection today?',
                created_at: new Date().toISOString()
              }
            ]);
          }
          setMessageCount(data.message_count);
          setDetectedCategory(data.detected_category);
          setLimitReached(data.message_count >= 10);
        })
        .catch(() => {
          initChat();
        });
    } else {
      initChat();
    }
  }, [chatId, initChat]);

  // Send message turn
  const sendMessage = async (content: string) => {
    if (!chatId) return;
    if (limitReached) return;

    const userTurn: ChatTurn = {
      role: 'user',
      content,
      created_at: new Date().toISOString()
    };

    setMessages((prev) => [...prev, userTurn]);
    setIsLoading(true);
    setError(null);

    try {
      const res = await sendChatMessage(chatId, content);
      const botTurn: ChatTurn = {
        role: 'assistant',
        content: res.reply,
        created_at: new Date().toISOString(),
        is_off_topic: !res.on_topic
      };

      setMessages((prev) => [...prev, botTurn]);
      setMessageCount(res.messages_used);
      if (res.detected_category) {
        setDetectedCategory(res.detected_category);
      }
      if (res.messages_used >= 10) {
        setLimitReached(true);
      }
    } catch (err: any) {
      if (err.message && err.message.includes('10-message limit')) {
        setLimitReached(true);
      }
      setError(err.message || 'Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };

  // Pre-fill form summarize
  const getSummary = async () => {
    if (!chatId) throw new Error('No active chat session');
    return await summarizeChat(chatId);
  };

  return {
    chatId,
    messages,
    messageCount,
    detectedCategory,
    isLoading,
    error,
    limitReached,
    sendMessage,
    getSummary,
    startNewChat: initChat
  };
}
