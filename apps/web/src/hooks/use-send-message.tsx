import { Message, MessageCreateInput } from '@/lib/api/generated-client';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { v4 as uuidv4 } from 'uuid';
import { toast } from 'sonner';

import { useCallback } from 'react';
import { useAtom } from 'jotai';
import useConfigurations from './use-configurations';

import { eventCountAtom, loadingAtom } from '@/atoms/messages';
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
  const setEventCount = useAtom(eventCountAtom)[1];

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

      let contentCache = '';

      setEventCount(0);

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
            setEventCount((prev) => prev + 1);

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
              console.log('message', ev.data);
              const message = messageSchema.parse(JSON.parse(ev.data));
              queryClient.setQueryData(
                getThreadMessagesQueryKey(threadId, activeConnection.name),
                (old: Message[]) => {
                  return [...old, message];
                }
              );
            }

            if (ev.event === 'content') {
              console.log('content', ev.data);
              const content = messageContentSchema.parse(JSON.parse(ev.data));
              if (content.type === 'text') {
                return;
              }

              queryClient.setQueryData(
                getThreadMessagesQueryKey(threadId, activeConnection.name),
                (old: Message[]) => {
                  if (content.type === 'text_delta') {
                    const messageContentIndex = old[
                      old.length - 1
                    ].content.findIndex((c) => c.id === content.id);

                    if (messageContentIndex !== -1) {
                      old[old.length - 1].content[messageContentIndex].text +=
                        content.delta;
                    } else {
                      old[old.length - 1].content.push({
                        type: 'text',
                        text: content.delta,
                        file_data: '',
                        file_name: '',
                        image_url: '',
                        tool_use_id: '',
                        name: '',
                        input: {},
                        output: '',
                        id: content.id,
                        delta: ''
                      });
                    }

                    console.log(old[old.length - 1].content);

                    return old;
                  }

                  return [
                    ...old.slice(0, -1),
                    {
                      ...message,
                      content: [...message.content, content]
                    }
                  ];
                }
              );
            }

            if (ev.event === 'content_start') {
              contentCache = '';
            }

            if (ev.event === 'content_delta') {
              contentCache += ev.data;
            }

            if (ev.event === 'content_end') {
              const content = messageContentSchema.parse(
                JSON.parse(contentCache)
              );

              if (content.type === 'text') {
                return;
              }

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
      setEventCount,
      setIsLoading
    ]
  );

  return { sendMessage, isLoading };
};

export default useSendMessage;
