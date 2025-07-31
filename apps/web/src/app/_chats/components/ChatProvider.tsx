'use client';

import { Chat } from '@ai-sdk/react';
import { useSuspenseQuery } from '@tanstack/react-query';
import {
  DefaultChatTransport,
  UIMessage,
  lastAssistantMessageIsCompleteWithToolCalls
} from 'ai';
import { createContext, useMemo } from 'react';
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

type AIChat = Chat<ChatMessage>;

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

  const { data: dbChat, refetch } = useSuspenseQuery(
    api.chats.getOrCreate.queryOptions({
      agentId: agentSlug
    })
  );

  const chat = useMemo(() => {
    return new Chat({
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
      }
    }) as AIChat;
  }, [dbChat.id, dbChat.messages, refetch, agentSlug]);

  return (
    <ChatContext.Provider value={{ chat }}>{children}</ChatContext.Provider>
  );
};

export default ChatProvider;
