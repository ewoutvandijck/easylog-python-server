import { MessageCreateInput } from '@/lib/api/generated-client';
import useConnections from './use-connections';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { toast } from 'sonner';

import { useCallback, useEffect } from 'react';
import { useAtom } from 'jotai';
import useConfigurations from './use-configurations';

import { messageContentSchema } from '@/app/schemas/message-contents';
import useThreadId from './use-thread-id';
import {
  assistantMessageAtom,
  loadingAtom,
  userMessageAtom
} from '@/atoms/messages';

const useSendMessage = () => {
  const { activeConnection } = useConnections();
  const { activeConfiguration } = useConfigurations();

  const [isLoading, setIsLoading] = useAtom(loadingAtom);

  const [userMessage, setUserMessage] = useAtom(userMessageAtom);
  const [assistantMessage, setAssistantMessage] = useAtom(assistantMessageAtom);

  const threadId = useThreadId();

  useEffect(() => {
    setAssistantMessage(null);
    setUserMessage(null);
  }, [setAssistantMessage, setUserMessage, threadId]);

  const sendMessage = useCallback(
    async (threadId: string, message: MessageCreateInput) => {
      setUserMessage({
        role: 'user' as const,
        contents: message.content.map((content) => ({
          type: 'text' as const,
          content: content.content
        }))
      });

      setIsLoading(true);

      const endpointURL = new URL(
        `${activeConnection.url}/threads/${threadId}/messages`
      );

      let toolResultBuffer: string | null = null;
      let toolResultBufferFormat: 'image' | 'unknown' | null = null;

      await new Promise(async (resolve, reject) => {
        await fetchEventSource(endpointURL.toString(), {
          method: 'POST',
          headers: {
            'X-API-KEY': activeConnection.secret,
            Authorization: `Bearer ${activeConfiguration?.easylogApiKey}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(message),
          onmessage(ev) {
            const data = JSON.parse(ev.data);

            if (ev.event === 'error') {
              toast.error(data.detail);
            }

            if (ev.event === 'delta') {
              const content = messageContentSchema.parse(data);

              setAssistantMessage((prev) => {
                const newContents = [...(prev?.contents ?? [])];
                const lastContent = newContents[newContents.length - 1];

                if (
                  content.type === 'text_delta' &&
                  lastContent?.type === 'text_delta'
                ) {
                  lastContent.content = lastContent.content + content.content;
                } else if (
                  content.type === 'text' &&
                  lastContent?.type === 'text_delta'
                ) {
                  // @ts-expect-error - TODO: fix this
                  lastContent.type = 'text';
                  lastContent.content = content.content;
                } else if (content.type === 'tool_result_delta') {
                  toolResultBuffer = (toolResultBuffer ?? '') + content.content;
                  toolResultBufferFormat = content.content_format;
                } else if (content.type === 'tool_result') {
                  content.content = toolResultBuffer ?? '';
                  content.content_format = toolResultBufferFormat ?? 'unknown';
                  toolResultBuffer = null;
                  toolResultBufferFormat = null;
                  newContents.push(content);
                } else {
                  newContents.push(content);
                }

                return {
                  role: 'assistant' as const,
                  contents: newContents
                };
              });
            }
          },
          onerror(ev) {
            setIsLoading(false);
            toast.error(ev.data);
            reject(ev);
          },
          async onopen() {
            setAssistantMessage(() => ({
              role: 'assistant',
              contents: []
            }));
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
      setUserMessage,
      setIsLoading,
      activeConnection.url,
      activeConnection.secret,
      activeConfiguration?.easylogApiKey,
      setAssistantMessage
    ]
  );

  return { sendMessage, isLoading, userMessage, assistantMessage };
};

export default useSendMessage;
