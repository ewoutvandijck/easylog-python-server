import { Message, MessageCreateInput } from '@/lib/api/generated-client';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { v4 as uuidv4 } from 'uuid';
import { toast } from 'sonner';

import { useCallback } from 'react';
import { useAtom } from 'jotai';
import useConfigurations from './use-configurations';

import { loadingAtom } from '@/atoms/messages';
import useApiClient from './use-api-client';
import { useQueryClient } from '@tanstack/react-query';
import { getThreadMessagesQueryKey } from './use-thread-messages';
import {
  messageContentSchema,
  messageSchema
} from '@/schemas/message-contents';

const useSendMessage = () => {
  const { activeConnection } = useApiClient();
  const { activeConfiguration } = useConfigurations();

  const [isLoading, setIsLoading] = useAtom(loadingAtom);
  const queryClient = useQueryClient();

  const sendMessage = useCallback(
    async (threadId: string, message: MessageCreateInput) => {
      queryClient.setQueryData(
        getThreadMessagesQueryKey(threadId, activeConnection.name),
        (old: Message[]) => {
          return [
            ...old,
            {
              id: uuidv4(),
              role: 'user',
              content: message.content.map((content) => ({
                id: uuidv4(),
                type: content.type,
                text: content.type === 'text' ? content.text : '',
                tool_use_id: '',
                name: '',
                input: {},
                output: '',
                image_url: content.type === 'image' ? content.image_url : '',
                file_data: content.type === 'file' ? content.file_data : '',
                file_name: content.type === 'file' ? content.file_name : '',
                delta: ''
              }))
            } satisfies Message
          ];
        }
      );

      setIsLoading(true);

      const endpointURL = new URL(
        `${activeConnection.url}/threads/${threadId}/messages`
      );

      await new Promise(async (resolve, reject) => {
        await fetchEventSource(endpointURL.toString(), {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${activeConnection.secret}`,
            'X-Easylog-Bearer-Token': `Bearer ${activeConfiguration?.easylogApiKey}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(message),
          onmessage(ev) {
            const data = JSON.parse(ev.data);

            if (ev.event === 'error') {
              toast.error(data.detail);
              queryClient.invalidateQueries({
                queryKey: getThreadMessagesQueryKey(
                  threadId,
                  activeConnection.name
                )
              });
            }

            if (ev.event === 'message') {
              const message = messageSchema.parse(JSON.parse(ev.data));
              queryClient.setQueryData(
                getThreadMessagesQueryKey(threadId, activeConnection.name),
                (old: Message[]) => {
                  return [...old, message];
                }
              );
            }

            if (ev.event === 'content') {
              const content = messageContentSchema.parse(JSON.parse(ev.data));
              queryClient.setQueryData(
                getThreadMessagesQueryKey(threadId, activeConnection.name),
                (old: Message[]) => {
                  return old.map((message) => {
                    return {
                      ...message,
                      content: [...message.content, content]
                    };
                  });
                }
              );
            }
          },
          onerror(ev) {
            setIsLoading(false);
            toast.error(ev.data);
            reject(ev);
          },
          async onopen() {
            setIsLoading(true);
          },
          async onclose() {
            setIsLoading(false);
            resolve(void 0);
          }
        });
      });
    },
    [
      activeConfiguration?.easylogApiKey,
      activeConnection.name,
      activeConnection.secret,
      activeConnection.url,
      queryClient,
      setIsLoading
    ]
  );

  return { sendMessage, isLoading };
};

export default useSendMessage;
