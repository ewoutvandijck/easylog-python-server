import { headers } from 'next/headers';
import { forbidden } from 'next/navigation';

import getCurrentUser from '@/app/_auth/data/getCurrentUser';
import ChatHistory from '@/app/_chat/components/ChatHistory';
import ChatInput from '@/app/_chat/components/ChatInput';
import ChatProvider from '@/app/_chat/components/ChatProvider';
import Header from '@/app/_shared/components/Header';

const ChatPage = async () => {
  const user = await getCurrentUser(await headers());

  if (!user) {
    throw forbidden();
  }

  return (
    <main className="flex h-svh flex-col">
      <Header user={user} />
      <ChatProvider>
        <ChatHistory />
        <ChatInput />
      </ChatProvider>
    </main>
  );
};

export default ChatPage;
