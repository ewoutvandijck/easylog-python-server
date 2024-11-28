import { useInfiniteQuery } from '@tanstack/react-query';
import useThreadId from './use-thread-id';
import useApiClient from './use-api-client';

const useThreadMessages = () => {
  const threadId = useThreadId();
  const { messages, activeConnection } = useApiClient();

  return useInfiniteQuery({
    queryKey: ['threadMessages', threadId, activeConnection.name],
    queryFn: async ({ pageParam = 0 }) => {
      return (
        await messages.getMessagesThreadsThreadIdMessagesGet({
          threadId: threadId!,
          limit: 100,
          offset: pageParam
        })
      ).data;
    },
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      return lastPage.length === 100 ? allPages.length * 100 : undefined;
    }
  });
};

export default useThreadMessages;
