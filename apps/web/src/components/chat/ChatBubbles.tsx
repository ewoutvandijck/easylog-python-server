'use client';

import useThreadMessages from '@/hooks/use-thread-messages';
import ChatBubble from './ChatBubble';
import { useRef, useEffect } from 'react';
import { useAtom } from 'jotai';
import { eventCountAtom } from '@/atoms/messages';

const ChatBubbles = () => {
  'use no memo';

  const scrollRef = useRef<HTMLDivElement>(null);

  const { data: messageData, isLoading } = useThreadMessages();

  const [eventCount] = useAtom(eventCountAtom);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current?.scrollHeight,
      behavior: 'smooth'
    });
  }, [messageData, eventCount]);

  if (isLoading) {
    return <div className="flex flex-col flex-1 gap-4">Loading...</div>;
  }

  return (
    <div
      className="h-full max-h-full overflow-y-auto flex flex-col gap-4 p-10"
      ref={scrollRef}
    >
      {messageData?.flatMap((message, messageIndex) =>
        message.content
          .filter(
            (content) =>
              !(
                content.type === 'tool_use' ||
                (content.type === 'tool_result' &&
                  (content.output === '{}' || content.output === 'None')) ||
                (content.type === 'text' && !content.text)
              )
          )
          .map((content, contentIndex) => (
            <ChatBubble
              key={`${messageIndex}-${contentIndex}`}
              content={content}
              role={
                message.role.toLowerCase() as
                  | 'user'
                  | 'assistant'
                  | 'system'
                  | 'developer'
                  | 'tool'
              }
            />
          ))
      )}
    </div>
  );
};

export default ChatBubbles;
