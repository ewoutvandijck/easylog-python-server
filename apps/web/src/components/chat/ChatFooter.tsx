'use client';

import { SendIcon } from 'lucide-react';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { z } from 'zod';
import useZodForm from '@/hooks/use-zod-form';
import useIsConnectionHealthy from '@/hooks/use-is-connection-healthy';

const schema = z.object({
  message: z.string().min(1)
});

const ChatFooter = () => {
  const { data: isConnected } = useIsConnectionHealthy();

  const form = useZodForm(schema);

  const onSubmit = (data: z.infer<typeof schema>) => {
    console.log(data);
  };

  return (
    <div className="flex justify-center gap-4 p-6">
      <form
        className="w-full flex gap-4 items-center max-w-lg"
        onSubmit={form.handleSubmit(onSubmit)}
      >
        <Textarea
          disabled={!isConnected}
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
          disabled={!isConnected}
          size="icon"
          className="w-16 h-10"
          variant="secondary"
          type="submit"
        >
          <SendIcon />
        </Button>
      </form>
    </div>
  );
};

export default ChatFooter;
