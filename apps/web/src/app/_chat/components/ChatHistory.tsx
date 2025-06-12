'use client';

import { useChat } from '@ai-sdk/react';
import { AnimatePresence, motion } from 'motion/react';

import ChatMessageAssistant from './ChatMessageAssistant';
import ChatMessageAssistantMarkdownContent from './ChatMessageAssistantMarkdownContent';
import ChatMessageUser from './ChatMessageUser';
import ChatMessageUserTextContent from './ChatMessageUserTextContent';
import useChatContext from '../hooks/useChatContext';

const ChatHistory = () => {
  const { chat } = useChatContext();

  const { status } = useChat({
    chat
  });

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-10">
      <div className="mx-auto max-w-2xl">
        <AnimatePresence>
          {chat.messages.map((message) =>
            message.role === 'user' ? (
              <ChatMessageUser key={message.id}>
                {message.parts.map(
                  (part) =>
                    part.type === 'text' && (
                      <ChatMessageUserTextContent
                        key={part.text}
                        text={part.text}
                      />
                    )
                )}
              </ChatMessageUser>
            ) : message.role === 'assistant' ? (
              <ChatMessageAssistant key={message.id}>
                {message.parts.map(
                  (part) =>
                    part.type === 'text' && (
                      <ChatMessageAssistantMarkdownContent
                        key={part.text}
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
              // exit={{ opacity: 0, scale: 0 }}
              transition={{ duration: 0.2 }}
            />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default ChatHistory;
