import { headers } from 'next/headers';
import { forbidden } from 'next/navigation';

import getCurrentUser from '@/app/_auth/data/getCurrentUser';
import ChatHistory from '@/app/_chats/components/ChatHistory';
import ChatInput from '@/app/_chats/components/ChatInput';
import ChatProvider from '@/app/_chats/components/ChatProvider';

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

  return (
    <ChatProvider agentSlug={agentSlug}>
      <ChatHistory />
      <ChatInput />
    </ChatProvider>
  );
};

export default ChatPage;
