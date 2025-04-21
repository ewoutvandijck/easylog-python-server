import { useQuery } from '@tanstack/react-query';
import useThreadId from './use-thread-id';
import useApiClient from './use-api-client';
import { messageSchema } from '@/schemas/messages';

export const getThreadMessagesQueryKey = (
  threadId: string,
  connectionName: string
) => ['threadMessages', threadId, connectionName];

const useThreadMessages = () => {
  const threadId = useThreadId();
  const { messages, activeConnection } = useApiClient();

  return useQuery({
    queryKey: getThreadMessagesQueryKey(threadId!, activeConnection.name),
    queryFn: async () => {
      const result = await messages.getMessagesThreadsThreadIdMessagesGet({
        threadId: threadId!,
        limit: 500,
        offset: 0,
        order: 'asc'
      });

      return result.data.map((message) => messageSchema.parse(message));
    }
  });
};

export default useThreadMessages;
