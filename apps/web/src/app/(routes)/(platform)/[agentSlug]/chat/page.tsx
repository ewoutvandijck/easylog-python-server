import { HydrationBoundary, dehydrate } from '@tanstack/react-query';
import { headers } from 'next/headers';
import { forbidden } from 'next/navigation';

import getCurrentUser from '@/app/_auth/data/getCurrentUser';
import ChatHistory from '@/app/_chats/components/ChatHistory';
import ChatInput from '@/app/_chats/components/ChatInput';
import ChatProvider from '@/app/_chats/components/ChatProvider';
import getQueryClient from '@/lib/react-query';
import api from '@/lib/trpc/server';

const ChatPage = async ({
  params
}: {
  params: Promise<{
    agentSlug: string;
  }>;
}) => {
  const { agentSlug } = await params;

  const user = await getCurrentUser(await headers());

  if (!user) {
    return forbidden();
  }

  const queryClient = getQueryClient();

  void queryClient.prefetchQuery(
    api.chats.getOrCreate.queryOptions({
      agentId: agentSlug
    })
  );

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <ChatProvider agentSlug={agentSlug}>
        <ChatHistory />
        <ChatInput />
      </ChatProvider>
    </HydrationBoundary>
  );
};

export default ChatPage;
