'use client';

import { Loader2Icon, SendIcon } from 'lucide-react';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { z } from 'zod';
import useZodForm from '@/hooks/use-zod-form';
import useIsConnectionHealthy from '@/hooks/use-is-connection-healthy';
import useSendMessage from '@/hooks/use-send-message';
import useThreadId from '@/hooks/use-thread-id';
import useConfigurations from '@/hooks/use-configurations';

const schema = z.object({
  message: z.string().min(1)
});

const ChatFooter = () => {
  const threadId = useThreadId();
  const { data: isConnected } = useIsConnectionHealthy();
  const { sendMessage, isLoading } = useSendMessage();
  const { activeConfiguration } = useConfigurations();

  const form = useZodForm(schema);

  const onSubmit = async (data: z.infer<typeof schema>) => {
    await sendMessage(threadId!, {
      agent_config: {
        agent_class: activeConfiguration?.agentConfig.agent_class ?? '',
        ...activeConfiguration?.agentConfig
      },
      content: [
        {
          text: data.message,
          type: 'text',
          file_data: '',
          file_name: '',
          image_url: ''
        }
      ]
    });
    form.reset();
  };

  return (
    <div className="flex justify-center gap-4 p-6 overflow-y-auto">
      <form
        className="w-full flex gap-4 items-center max-w-lg"
        onSubmit={form.handleSubmit(onSubmit)}
      >
        <Textarea
          autoFocus
          disabled={!isConnected || form.formState.isSubmitting}
          style={{ fieldSizing: 'content' } as React.CSSProperties}
          placeholder="Type a message..."
          className="min-h-10 max-h-40 max-w-full"
          {...form.register('message')}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              form.handleSubmit(onSubmit)();
            }
          }}
        />
        <Button
          disabled={!isConnected || form.formState.isSubmitting || isLoading}
          size="icon"
          className="w-16 h-10"
          variant="secondary"
          type="submit"
        >
          {isLoading ? <Loader2Icon className="animate-spin" /> : <SendIcon />}
        </Button>
      </form>
    </div>
  );
};

export default ChatFooter;
