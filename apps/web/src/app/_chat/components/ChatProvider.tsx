'use client';

import { Chat } from '@ai-sdk/react';
import { UIDataPartSchemas } from 'ai';
import { createContext, useState } from 'react';

interface ChatContextType {
  chat: Chat<unknown, UIDataPartSchemas>;
}

export const ChatContext = createContext<ChatContextType | undefined>(
  undefined
);

interface ChatProviderProps {}

const ChatProvider = ({
  children
}: React.PropsWithChildren<ChatProviderProps>) => {
  const [chat] = useState(
    new Chat({
      messages: []
    })
  );

  return (
    <ChatContext.Provider value={{ chat }}>{children}</ChatContext.Provider>
  );
};

export default ChatProvider;
