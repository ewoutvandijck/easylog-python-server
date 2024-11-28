'use client';

import useThreadMessages from '@/hooks/use-thread-messages';
import ChatBubble from './ChatBubble';
import useSendMessage from '@/hooks/use-send-message';
import { useRef, useEffect } from 'react';

const ChatBubbles = () => {
  const scrollRef = useRef<HTMLDivElement>(null);

  const { data: messageData, isLoading } = useThreadMessages();

  const { assistantMessage, userMessage } = useSendMessage();

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current?.scrollHeight,
      behavior: 'smooth'
    });
  }, [messageData, assistantMessage, userMessage]);

  if (isLoading)
    return <div className="flex flex-col flex-1 gap-4">Loading...</div>;

  return (
    <div
      className="h-full max-h-full overflow-y-auto flex flex-col gap-4 p-10"
      ref={scrollRef}
    >
      {messageData?.pages.map((page) =>
        page.map((message) => (
          <ChatBubble
            key={message.id}
            contents={message.contents!}
            role={message.role as 'user' | 'assistant'}
          />
        ))
      )}
      {userMessage && (
        <ChatBubble contents={userMessage.contents} role="user" />
      )}
      {assistantMessage && (
        <ChatBubble contents={assistantMessage.contents} role="assistant" />
      )}
    </div>
  );
};

export default ChatBubbles;
