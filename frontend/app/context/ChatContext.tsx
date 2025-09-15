"use client";

import { createContext, useState, useContext, ReactNode } from 'react';

interface ChatContextType {
  ticker: string | null;
  setTicker: (ticker: string | null) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatContextProvider = ({ children }: { children: ReactNode }) => {
  const [ticker, setTicker] = useState<string | null>(null);

  return (
    <ChatContext.Provider value={{ ticker, setTicker }}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChatContext = () => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChatContext must be used within a ChatContextProvider');
  }
  return context;
};
