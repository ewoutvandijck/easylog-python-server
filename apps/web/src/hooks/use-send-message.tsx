import { MessageCreateInput } from '@/lib/api/generated-client';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { v4 as uuidv4 } from 'uuid';
import { toast } from 'sonner';

import { useAtom } from 'jotai';
import useConfigurations from './use-configurations';

import { eventCountAtom, loadingAtom } from '@/atoms/messages';
import useApiClient from './use-api-client';
import { useQueryClient } from '@tanstack/react-query';
import { getThreadMessagesQueryKey } from './use-thread-messages';
import {
  Message,
  MessageContent,
  messageContentSchema,
  messageSchema
} from '@/schemas/messages';

const useSendMessage = () => {
  const { activeConnection } = useApiClient();
  const { activeConfiguration } = useConfigurations();

  const [isLoading, setIsLoading] = useAtom(loadingAtom);
  const setEventCount = useAtom(eventCountAtom)[1];

  const queryClient = useQueryClient();

  const sendMessage = async (threadId: string, message: MessageCreateInput) => {
    setIsLoading(true);
    setEventCount(0);
    let contentCache = '';

    const endpointURL = new URL(
      `${activeConnection.url}/threads/${threadId}/messages`
    );

    const queryKey = getThreadMessagesQueryKey(threadId, activeConnection.name);

    const handleMessageContent = (content: MessageContent) => {
      queryClient.setQueryData(queryKey, (old: Message[] = []) => {
        if (old.length === 0) return old;

        const lastMessage = old[old.length - 1];

        if (
          content.type === 'text' &&
          lastMessage.content.find((c) => c.id === content.id)
        ) {
          return old;
        }

        const matchingContent = lastMessage.content.findIndex(
          (c) => c.id === content.id
        );

        if (
          content.type === 'text_delta' &&
          matchingContent !== -1 &&
          lastMessage.content[matchingContent].type === 'text'
        ) {
          lastMessage.content[matchingContent].text += content.delta;
        } else if (content.type === 'text_delta') {
          lastMessage.content.push({
            ...content,
            type: 'text',
            text: content.delta
          });
        } else {
          lastMessage.content.push(content);
        }

        return old;
      });
    };

    queryClient.setQueryData(queryKey, (old: Message[] = []) => {
      return [
        ...old,
        {
          id: uuidv4(),
          role: 'user',
          content: message.content
        }
      ];
    });

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
            queryClient.invalidateQueries({ queryKey });
          }

          if (ev.event === 'message') {
            console.log('message', ev.data);
            queryClient.setQueryData(queryKey, (old: Message[] = []) => {
              return [...old, messageSchema.parse(JSON.parse(ev.data))];
            });
          }

          if (ev.event === 'content') {
            handleMessageContent(
              messageContentSchema.parse(JSON.parse(ev.data))
            );
          }

          if (ev.event === 'content_start') {
            contentCache = '';
          }

          if (ev.event === 'content_delta') {
            contentCache += ev.data;
          }

          if (ev.event === 'content_end') {
            handleMessageContent(
              messageContentSchema.parse(JSON.parse(contentCache))
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
  };

  return { sendMessage, isLoading };
};

export default useSendMessage;
