import React from 'react';
import { MessageSquarePlus } from 'lucide-react';

interface ChatLauncherProps {
  onClick: () => void;
  isOpen: boolean;
}

export const ChatLauncher: React.FC<ChatLauncherProps> = ({ onClick, isOpen }) => {
  if (isOpen) return null;

  return (
    <button
      onClick={onClick}
      aria-label="Open network assistant"
      className="fixed bottom-6 right-6 bg-mnnit-blue hover:bg-blue-800 text-white p-4 rounded-full shadow-2xl flex items-center gap-2.5 transition-transform hover:scale-105 active:scale-95 z-40 focus:outline-none focus:ring-4 focus:ring-blue-300"
    >
      <MessageSquarePlus className="w-6 h-6 text-mnnit-gold" />
      <span className="font-semibold text-sm hidden sm:inline">Network Assistant</span>
    </button>
  );
};
