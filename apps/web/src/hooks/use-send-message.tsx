import {
  MessageContents,
  MessageCreateInput,
  MessageCreateInputContentInner
} from '@/lib/api/generated-client';
import useConnections from './use-connections';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { toast } from 'sonner';
import useThreadMessages from './use-thread-messages';
import { useCallback } from 'react';
import { atom, useAtom } from 'jotai';
import useConfigurations from './use-configurations';

const assistantMessageAtom = atom<{
  role: 'assistant';
  contents: MessageContents[];
} | null>(null);
const userMessageAtom = atom<{
  role: 'user';
  contents: MessageCreateInputContentInner[];
} | null>(null);
const loadingAtom = atom<boolean>(false);

const useSendMessage = () => {
  const { activeConnection } = useConnections();
  const { activeConfiguration } = useConfigurations();

  const { refetch } = useThreadMessages();

  const [assistantMessage, setAssistantMessage] = useAtom(assistantMessageAtom);
  const [userMessage, setUserMessage] = useAtom(userMessageAtom);
  const [isLoading, setIsLoading] = useAtom(loadingAtom);

  const sendMessage = useCallback(
    async (threadId: string, message: MessageCreateInput) => {
      setUserMessage({
        role: 'user',
        contents: message.content
      });

      setIsLoading(true);

      const endpointURL = new URL(
        `${activeConnection.url}/threads/${threadId}/messages`
      );

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
              setAssistantMessage((prev) => ({
                role: 'assistant',
                contents: [...(prev?.contents ?? []), data]
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
        });
      });
    },
    [
      activeConnection.secret,
      activeConnection.url,
      activeConfiguration?.easylogApiKey,
      refetch,
      setAssistantMessage,
      setIsLoading,
      setUserMessage
    ]
  );

  return { sendMessage, assistantMessage, userMessage, isLoading };
};

export default useSendMessage;
