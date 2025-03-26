'use client';

import useThreadMessages from '@/hooks/use-thread-messages';
import ChatBubble from './ChatBubble';
import { useRef, useEffect } from 'react';

import useSendMessage from '@/hooks/use-send-message';

const ChatBubbles = () => {
  const scrollRef = useRef<HTMLDivElement>(null);

  const { data: messageData, isLoading } = useThreadMessages();
  const { userMessage, assistantMessage } = useSendMessage();

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current?.scrollHeight,
      behavior: 'smooth'
    });
  }, [messageData]);

  if (isLoading)
    return <div className="flex flex-col flex-1 gap-4">Loading...</div>;

  return (
    <div
      className="h-full max-h-full overflow-y-auto flex flex-col gap-4 p-10"
      ref={scrollRef}
    >
      {messageData?.pages
        .flatMap((page) => page)
        .map((message, messageIndex) => (
          <ChatBubble
            key={`${messageIndex}`}
            contents={message.contents}
            role={message.role}
          />
        ))}

      {userMessage && (
        <ChatBubble
          key={`${userMessage.role}`}
          contents={userMessage.contents}
          role={userMessage.role}
        />
      )}

      {assistantMessage && (
        <ChatBubble
          key={`${assistantMessage.role}`}
          contents={assistantMessage.contents}
          role={assistantMessage.role}
        />
      )}
    </div>
  );
};

export default ChatBubbles;
