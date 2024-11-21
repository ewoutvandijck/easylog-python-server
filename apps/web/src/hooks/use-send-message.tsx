import {
  CreateMessageThreadsThreadIdMessagesPostRequest
  // PaginationMessages
} from '@/lib/api/generated-client';
// import useApiClient from './use-api-client';
import useConnections from './use-connections';
import {
  // InfiniteData,
  useMutation
  // useQueryClient
} from '@tanstack/react-query';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { toast } from 'sonner';
import useThreadMessages from './use-thread-messages';

const useSendMessage = () => {
  const { activeConnection } = useConnections();

  const { refetch } = useThreadMessages();
  // const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (
      params: CreateMessageThreadsThreadIdMessagesPostRequest
    ) => {
      await new Promise(async (resolve, reject) => {
        await fetchEventSource(
          `${activeConnection.url}/threads/${params.threadId}/messages`,
          {
            method: 'POST',
            headers: {
              'X-API-KEY': activeConnection.secret,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(params.messageCreateInput),
            onmessage(ev) {
              const data = JSON.parse(ev.data);

              if (ev.event === 'error') {
                toast.error(data.detail);
              }

              if (ev.event === 'delta') {
                // queryClient.setQueryData(
                //   ['threadMessages', params.threadId],
                //   (messages: InfiniteData<PaginationMessages, unknown>) => {
                //     const lastPage = messages.pages[messages.pages.length - 1];
                //     const newMessages = lastPage.data.concat(data.content);
                //     return {
                //       ...messages,
                //       pages: [...messages.pages, { data: newMessages }]
                //     };
                //   }
                // );
              }
            },
            onerror(ev) {
              toast.error(ev.data);
              reject(ev);
            },
            onclose() {
              refetch();
              resolve(void 0);
            }
          }
        );
      });

      return '';
    },
    retry: false
  });
};

export default useSendMessage;
