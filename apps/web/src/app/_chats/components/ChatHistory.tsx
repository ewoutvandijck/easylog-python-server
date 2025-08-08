'use client';

import { AnimatePresence, motion } from 'motion/react';
import { useCallback, useEffect, useRef, useState } from 'react';

import ChatMessageAssistant from './ChatMessageAssistant';
import ChatMessageAssistantChart from './ChatMessageAssistantChart';
import ChatMessageAssistantDocumentSearch from './ChatMessageAssistantDocumentSearch';
import ChatMessageAssistantMarkdownContent from './ChatMessageAssistantMarkdownContent';
import ChatMessageUser from './ChatMessageUser';
import ChatMessageUserTextContent from './ChatMessageUserTextContent';
import useChatContext from '../hooks/useChatContext';

const BOTTOM_THRESHOLD_PX = 56;

const ChatHistory = () => {
  const [isPinnedToBottom, setIsPinnedToBottom] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const { messages, status } = useChatContext();

  const isAtBottom = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return true;
    const distance = el.scrollHeight - (el.scrollTop + el.clientHeight);
    return distance <= BOTTOM_THRESHOLD_PX;
  }, []);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior });
  }, []);

  useEffect(() => {
    scrollToBottom('auto');
  }, [scrollToBottom]);

  useEffect(() => {
    if (!isPinnedToBottom) return;
    scrollToBottom('smooth');
  }, [messages, status, isPinnedToBottom, scrollToBottom]);

  const handleScroll = () => {
    setIsPinnedToBottom(isAtBottom());
  };

  return (
    <div
      className="relative flex-1 overflow-y-auto p-3 md:p-10"
      ref={scrollRef}
      onScroll={handleScroll}
    >
      <div className="mx-auto max-w-2xl">
        <AnimatePresence>
          {messages.map((message) =>
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
                {message.parts.map((part, i) =>
                  part.type === 'text' ? (
                    <ChatMessageAssistantMarkdownContent
                      key={`${message.id}-${i}`}
                      text={part.text}
                    />
                  ) : part.type === 'data-chart' ? (
                    <ChatMessageAssistantChart
                      key={`${message.id}-${i}`}
                      config={part.data}
                    />
                  ) : part.type === 'data-document-search' ? (
                    <ChatMessageAssistantDocumentSearch
                      key={`${message.id}-${i}`}
                      status={part.data.status}
                      content={part.data.content}
                    />
                  ) : null
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
