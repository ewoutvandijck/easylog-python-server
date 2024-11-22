import { useInfiniteQuery } from '@tanstack/react-query';
import useThreadId from './use-thread-id';
import useApiClient from './use-api-client';

const useThreadMessages = () => {
  const threadId = useThreadId();
  const { messages, activeConnection } = useApiClient();

  return useInfiniteQuery({
    queryKey: ['threadMessages', threadId, activeConnection.name],
    queryFn: ({ pageParam = 0 }) =>
      messages.getMessagesThreadsThreadIdMessagesGet({
        threadId: threadId!,
        limit: 100,
        offset: pageParam
      }),
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      return lastPage.data.length === 100 ? allPages.length * 100 : undefined;
    }
  });
};

export default useThreadMessages;
