'use client';

import { Chat } from '@ai-sdk/react';
import { UIMessage } from 'ai';
import { createContext, useState } from 'react';
import z from 'zod';

import internalChartConfigSchema from '@/app/_charts/schemas/internalChartConfigSchema';

type AIChat = Chat<
  UIMessage<
    unknown,
    {
      chart: z.infer<typeof internalChartConfigSchema>;
    }
  >
>;

interface ChatContextType {
  chat: AIChat;
}

export const ChatContext = createContext<ChatContextType | undefined>(
  undefined
);

interface ChatProviderProps {}

const ChatProvider = ({
  children
}: React.PropsWithChildren<ChatProviderProps>) => {
  const [chat] = useState<AIChat>(
    new Chat({
      maxSteps: 5,
      dataPartSchemas: {
        chart: internalChartConfigSchema
      }
    })
  );

  return (
    <ChatContext.Provider value={{ chat }}>{children}</ChatContext.Provider>
  );
};

export default ChatProvider;
