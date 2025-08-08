'use client';

import { UseChatHelpers, useChat } from '@ai-sdk/react';
import { useSuspenseQuery } from '@tanstack/react-query';
import {
  DefaultChatTransport,
  UIMessage,
  lastAssistantMessageIsCompleteWithToolCalls
} from 'ai';
import { createContext } from 'react';
import z from 'zod';

import internalChartConfigSchema from '@/app/_charts/schemas/internalChartConfigSchema';
import useTRPC from '@/lib/trpc/browser';

import documentSearchSchema from '../schemas/documentSearchSchema';

type ChatMessage = UIMessage<
  unknown,
  {
    chart: z.infer<typeof internalChartConfigSchema>;
    'document-search': z.infer<typeof documentSearchSchema>;
  }
>;

interface ChatContextType extends UseChatHelpers<ChatMessage> {}

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

  const { data: dbChat, refetch } = useSuspenseQuery(
    api.chats.getOrCreate.queryOptions({
      agentId: agentSlug
    })
  );

  const chat = useChat({
    id: dbChat.id,
    transport: new DefaultChatTransport({
      api: `/api/${agentSlug}/chat`,
      prepareSendMessagesRequest({ messages, id }) {
        return {
          body: { message: messages[messages.length - 1], id }
        };
      }
    }),
    messages: dbChat.messages as ChatMessage[],
    sendAutomaticallyWhen: (args) => {
      return lastAssistantMessageIsCompleteWithToolCalls(args);
    },
    dataPartSchemas: {
      chart: internalChartConfigSchema,
      'document-search': documentSearchSchema
    },
    onToolCall: async ({ toolCall }) => {
      if (toolCall.toolName === 'clearChat') {
        await refetch();
      }
    },
    experimental_throttle: 50
  });

  return <ChatContext.Provider value={chat}>{children}</ChatContext.Provider>;
};

export default ChatProvider;
