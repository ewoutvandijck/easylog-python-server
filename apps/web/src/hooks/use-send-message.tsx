import { MessageCreateInput } from '@/lib/api/generated-client';
import useConnections from './use-connections';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { toast } from 'sonner';
import useThreadMessages from './use-thread-messages';
import { useCallback } from 'react';
import { atom, useAtom } from 'jotai';

type PartialMessageContent = {
  type: 'text';
  content: string;
};

type PartialMessage = {
  role: 'assistant' | 'user';
  contents: PartialMessageContent[];
};

const assistantMessageAtom = atom<PartialMessage | null>(null);
const userMessageAtom = atom<PartialMessage | null>(null);
const loadingAtom = atom<boolean>(false);

const useSendMessage = () => {
  const { activeConnection } = useConnections();

  const { refetch } = useThreadMessages();

  const [assistantMessage, setAssistantMessage] = useAtom(assistantMessageAtom);
  const [userMessage, setUserMessage] = useAtom(userMessageAtom);
  const [isLoading, setIsLoading] = useAtom(loadingAtom);

  const sendMessage = useCallback(
    async (threadId: string, message: MessageCreateInput) => {
      setUserMessage({
        role: 'user',
        contents: message.content.map((content) => ({
          type: 'text',
          content: content.content
        }))
      });

      setIsLoading(true);

      await new Promise(async (resolve, reject) => {
        await fetchEventSource(
          `${activeConnection.url}/threads/${threadId}/messages`,
          {
            method: 'POST',
            headers: {
              'X-API-KEY': activeConnection.secret,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(message),
            onmessage(ev) {
              const data = JSON.parse(ev.data);

              if (ev.event === 'error') {
                toast.error(data.detail);
              }

              if (ev.event === 'delta') {
                setAssistantMessage((prev) => ({
                  role: 'assistant',
                  contents: [
                    ...(prev?.contents ?? []),
                    { type: 'text', content: data.content }
                  ]
                }));
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
              await refetch();
              setIsLoading(false);
              setAssistantMessage(null);
              setUserMessage(null);
              resolve(void 0);
            }
          }
        );
      });
    },
    [
      activeConnection.secret,
      activeConnection.url,
      refetch,
      setAssistantMessage,
      setIsLoading,
      setUserMessage
    ]
  );

  return { sendMessage, assistantMessage, userMessage, isLoading };
};

export default useSendMessage;
