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
import useConnections from '@/hooks/use-connections';
import useZodForm from '@/hooks/use-zod-form';
import { cn } from '@/lib/utils';
import { useState } from 'react';
import { toast } from 'sonner';
import { z } from 'zod';

const schema = z.object({
  name: z.string().min(1),
  url: z.string().url().min(1),
  secret: z.string().min(1)
});

const ConnectionAddDialog = ({ children }: React.PropsWithChildren) => {
  const [isOpen, setIsOpen] = useState(false);
  const { connections, addConnection, setActiveConnection } = useConnections();
  const form = useZodForm(schema, {
    defaultValues: {
      name: 'localhost',
      url: 'http://127.0.0.1:8000/api/v1',
      secret: 'secret'
    }
  });

  const onSubmit = (data: z.infer<typeof schema>) => {
    if (connections.find((c) => c.name === data.name)) {
      toast.error('Connection already exists, choose a different name');
      return;
    }

    toast.success('Connection added');
    addConnection(data);
    setActiveConnection(data.name);
    setIsOpen(false);
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Add connection</DialogTitle>
            <DialogDescription>
              Add a new connection to your workspace.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="name" className="text-right">
                Name
              </Label>
              <div className="flex flex-col gap-1.5 col-span-3">
                <Input
                  id="name"
                  {...form.register('name')}
                  className="col-span-3"
                />
                <p
                  className={cn(
                    'text-[0.8rem] font-medium text-destructive',
                    form.formState.errors.name && 'visible'
                  )}
                >
                  {form.formState.errors.name?.message}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="url" className="text-right">
                URL
              </Label>
              <div className="flex flex-col gap-1.5 col-span-3">
                <Input
                  id="url"
                  {...form.register('url')}
                  className="col-span-3"
                />
                <p
                  className={cn(
                    'text-[0.8rem] font-medium text-destructive',
                    form.formState.errors.url && 'visible'
                  )}
                >
                  {form.formState.errors.url?.message}
                </p>
              </div>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="secret" className="text-right">
                Secret
              </Label>
              <div className="flex flex-col gap-1.5 col-span-3">
                <Input
                  id="secret"
                  {...form.register('secret')}
                  className="col-span-3"
                />
                <p
                  className={cn(
                    'text-[0.8rem] font-medium text-destructive',
                    form.formState.errors.secret && 'visible'
                  )}
                >
                  {form.formState.errors.secret?.message}
                </p>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button type="submit">Add connection</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default ConnectionAddDialog;
