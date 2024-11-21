import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import useApiClient from '@/hooks/use-api-client';

import useThreads from '@/hooks/use-threads';
import useZodForm from '@/hooks/use-zod-form';
import { CreateThreadThreadsPostRequest } from '@/lib/api/generated-client';
import { cn } from '@/lib/utils';
import { useMutation } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { toast } from 'sonner';
import { z } from 'zod';

const schema = z.object({
  external_id: z.string().min(1)
});

const ChatNewDialog = ({ children }: React.PropsWithChildren) => {
  const [isOpen, setIsOpen] = useState(false);
  const router = useRouter();

  const { refetch: refetchThreads } = useThreads();
  const apiClient = useApiClient();

  const { mutateAsync: createThread } = useMutation({
    mutationFn: (params: CreateThreadThreadsPostRequest) =>
      apiClient.threads.createThreadThreadsPost(params),
    onSuccess: (data) => {
      refetchThreads();
      setIsOpen(false);
      router.push(`/${data.external_id}`);
      toast.success('Chat created');
    }
  });

  const form = useZodForm(schema, {
    defaultValues: {
      external_id: ''
    }
  });

  const onSubmit = async (data: z.infer<typeof schema>) => {
    await createThread({
      chatCreateInput: {
        external_id: data.external_id
      }
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>New chat</DialogTitle>
            <DialogDescription>Start a new chat</DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-3 py-4 w-full">
            <Label htmlFor="name">Name</Label>
            <div className="flex flex-col gap-1.5 col-span-3">
              <Label htmlFor="name" className="text-right">
                Name
              </Label>
              <div className="flex flex-col gap-1.5 col-span-3">
                <Input
                  id="external_id"
                  {...form.register('external_id')}
                  className="col-span-3"
                />
                <p
                  className={cn(
                    'text-[0.8rem] font-medium text-destructive',
                    form.formState.errors.external_id && 'visible'
                  )}
                >
                  {form.formState.errors.external_id?.message}
                </p>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button type="submit">Create chat</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default ChatNewDialog;
