import { useInfiniteQuery } from '@tanstack/react-query';
import useThreadId from './use-thread-id';
import useApiClient from './use-api-client';
import { Message } from '@/app/schemas/messages';
import { useAtom } from 'jotai';
import { assistantMessageAtom, userMessageAtom } from '@/atoms/messages';

const useThreadMessages = () => {
  const threadId = useThreadId();
  const { messages, activeConnection } = useApiClient();

  const [userMessage] = useAtom(userMessageAtom);
  const [assistantMessage] = useAtom(assistantMessageAtom);

  const query = useInfiniteQuery({
    queryKey: ['threadMessages', threadId, activeConnection.name],
    queryFn: async ({ pageParam = 0 }) => {
      const messageData = await messages.getMessagesThreadsThreadIdMessagesGet({
        threadId: threadId!,
        limit: 100,
        offset: pageParam
      });

      return messageData.data.map((message) => message as Message);
    },
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      return lastPage.length === 100 ? allPages.length * 100 : undefined;
    }
  });

  // Create a derived data object that includes all pages of messages plus
  // the current user and assistant messages if they exist
  const allMessages = query.data ? query.data.pages.flat() : [];

  // Create final messages array with local messages appended
  const messagesWithLocal = [...allMessages];

  // Add user message if it exists
  if (userMessage) {
    messagesWithLocal.push(userMessage);
  }

  // Add assistant message if it exists
  if (assistantMessage) {
    messagesWithLocal.push(assistantMessage);
  }

  return {
    ...query,
    data: messagesWithLocal
  };
};

export default useThreadMessages;
