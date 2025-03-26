import { useInfiniteQuery } from '@tanstack/react-query';
import useThreadId from './use-thread-id';
import useApiClient from './use-api-client';
import { Message } from '@/app/schemas/messages';

const useThreadMessages = () => {
  const threadId = useThreadId();
  const { messages, activeConnection } = useApiClient();

  return useInfiniteQuery({
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
};

export default useThreadMessages;
