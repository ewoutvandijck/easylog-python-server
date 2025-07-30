'use client';

import { Chat } from '@ai-sdk/react';
import { useSuspenseQuery } from '@tanstack/react-query';
import { DefaultChatTransport, UIMessage } from 'ai';
import { createContext, useState } from 'react';
import z from 'zod';

import internalChartConfigSchema from '@/app/_charts/schemas/internalChartConfigSchema';
import useTRPC from '@/lib/trpc/browser';

import documentSearchSchema from '../schemas/documentSearchSchema';

type AIChat = Chat<
  UIMessage<
    unknown,
    {
      chart: z.infer<typeof internalChartConfigSchema>;
      'document-search': z.infer<typeof documentSearchSchema>;
    }
  >
>;

interface ChatContextType {
  chat: AIChat;
}

export const ChatContext = createContext<ChatContextType | undefined>(
  undefined
);

interface ChatProviderProps {
  agentSlug: string;
}

const ChatProvider = ({
  children,
  agentSlug
}: React.PropsWithChildren<ChatProviderProps>) => {
  const api = useTRPC();

  const { data: dbChat } = useSuspenseQuery(
    api.chats.getOrCreate.queryOptions({
      agentId: agentSlug
    })
  );

  const [chat] = useState<AIChat>(
    new Chat({
      id: dbChat.id,
      transport: new DefaultChatTransport(),
      dataPartSchemas: {
        chart: internalChartConfigSchema,
        'document-search': documentSearchSchema
      }
    })
  );

  return (
    <ChatContext.Provider value={{ chat }}>{children}</ChatContext.Provider>
  );
};

export default ChatProvider;
