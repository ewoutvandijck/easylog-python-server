'use client';

import { useChat } from '@ai-sdk/react';
import { AnimatePresence, motion } from 'motion/react';
import { useEffect, useRef } from 'react';

import ChatMessageAssistant from './ChatMessageAssistant';
import ChatMessageAssistantMarkdownContent from './ChatMessageAssistantMarkdownContent';
import ChatMessageUser from './ChatMessageUser';
import ChatMessageUserTextContent from './ChatMessageUserTextContent';
import useChatContext from '../hooks/useChatContext';

const ChatHistory = () => {
  /** TODO: pin scroll to bottom when new message is submitted */
  const scrollRef = useRef<HTMLDivElement>(null);

  const { chat } = useChatContext();
  const { status } = useChat({ chat });

  useEffect(() => {
    if (!scrollRef.current) return;
    if (status !== 'submitted') return;

    scrollRef.current.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: 'smooth'
    });
  }, [status]);

  return (
    <div
      className="relative flex-1 overflow-y-auto p-3 md:p-10"
      ref={scrollRef}
    >
      <div className="mx-auto max-w-2xl">
        <AnimatePresence>
          {chat.messages.map((message) =>
            message.role === 'user' ? (
              <ChatMessageUser key={message.id}>
                {message.parts.map(
                  (part, i) =>
                    part.type === 'text' && (
                      <ChatMessageUserTextContent
                        key={`${message.id}-${i}`}
                        text={part.text}
                      />
                    )
                )}
              </ChatMessageUser>
            ) : message.role === 'assistant' ? (
              <ChatMessageAssistant key={message.id}>
                {message.parts.map(
                  (part, i) =>
                    part.type === 'text' && (
                      <ChatMessageAssistantMarkdownContent
                        key={`${message.id}-${i}`}
                        text={part.text}
                      />
                    )
                )}
              </ChatMessageAssistant>
            ) : null
          )}

          {status === 'submitted' && (
            <motion.div
              className="bg-fill-brand animate-scale-in size-3 rounded-full"
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.2 }}
            />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default ChatHistory;
