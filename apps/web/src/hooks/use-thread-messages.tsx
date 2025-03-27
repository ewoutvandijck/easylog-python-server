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

  if (!userMessage || !assistantMessage) {
    return query;
  }

  return {
    ...query,
    data: query.data
      ? {
          ...query.data,
          pages: [
            ...(query.data.pages.length > 1
              ? query.data.pages.slice(0, -1)
              : []),
            [
              ...(query.data.pages.length > 0
                ? query.data.pages[query.data.pages.length - 1]
                : []),
              userMessage,
              assistantMessage
            ]
          ]
        }
      : {
          pages: [[userMessage, assistantMessage]],
          pageParams: [0]
        }
  };
};

export default useThreadMessages;
