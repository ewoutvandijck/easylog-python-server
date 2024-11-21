'use client';

import useThreadMessages from '@/hooks/use-thread-messages';
import ChatBubble from './ChatBubble';

const ChatBubbles = () => {
  const { data: messageData, isLoading } = useThreadMessages();

  if (isLoading)
    return <div className="flex flex-col flex-1 gap-4">Loading...</div>;

  return (
    <div className="h-full max-h-full overflow-y-auto flex flex-col gap-4 p-10">
      {messageData?.pages.map((page) =>
        page.data.map((message) => (
          <ChatBubble
            key={message.id}
            contents={message.contents!}
            role={message.role as 'user' | 'assistant'}
          />
        ))
      )}
    </div>
  );
};

export default ChatBubbles;
