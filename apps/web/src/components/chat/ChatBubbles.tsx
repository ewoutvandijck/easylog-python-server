'use client';

import useThreadMessages from '@/hooks/use-thread-messages';
import ChatBubble from './ChatBubble';
import { useRef, useEffect } from 'react';

const ChatBubbles = () => {
  const scrollRef = useRef<HTMLDivElement>(null);

  const { data: messageData, isLoading } = useThreadMessages();

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current?.scrollHeight,
      behavior: 'smooth'
    });
  }, [messageData]);

  if (isLoading) {
    return <div className="flex flex-col flex-1 gap-4">Loading...</div>;
  }

  return (
    <div
      className="h-full max-h-full overflow-y-auto flex flex-col gap-4 p-10"
      ref={scrollRef}
    >
      {messageData?.flatMap((message, messageIndex) =>
        message.contents
          .filter((content) => {
            if (content.type === 'text') {
              return true;
            }

            if (content.type === 'text_delta') {
              return true;
            }

            if (
              content.type === 'tool_result' &&
              (content.content_format === 'image' ||
                content.content_format === 'chart')
            ) {
              message.role = 'assistant';
              return true;
            }

            return false;
          })
          .map((content, contentIndex) => (
            <ChatBubble
              key={`${messageIndex}-${contentIndex}`}
              content={content}
              role={message.role}
            />
          ))
      )}
    </div>
  );
};

export default ChatBubbles;
