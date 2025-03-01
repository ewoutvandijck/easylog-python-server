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

import useZodForm from '@/hooks/use-zod-form';

import { useState } from 'react';
import { toast } from 'sonner';
import { z } from 'zod';

import { JsonEditor } from 'json-edit-react';
import { Controller } from 'react-hook-form';
import useConfigurations from '@/hooks/use-configurations';

const schema = z.object({
  name: z.string(),
  agentConfig: z
    .object({
      agent_class: z.string()
    })
    .and(z.record(z.any())),
  easylogApiKey: z.string().default('')
});

export interface ConfigurationUpdateDialogProps {
  configurationName: string;
}

const ConfigurationUpdateDialog = ({
  configurationName,
  children
}: React.PropsWithChildren<ConfigurationUpdateDialogProps>) => {
  const { configurations, updateConfiguration, setActiveConfiguration } =
    useConfigurations();

  const configuration = configurations.find(
    (config) => config.name === configurationName
  );

  const [isOpen, setIsOpen] = useState(false);

  const form = useZodForm(schema, {
    defaultValues: {
      name: configuration?.name ?? '',
      agentConfig: configuration?.agentConfig ?? {},
      easylogApiKey: configuration?.easylogApiKey ?? ''
    }
  });

  const onSubmit = async (data: z.infer<typeof schema>) => {
    updateConfiguration(configurationName, data);
    setActiveConfiguration(data.name);
    setIsOpen(false);
    toast.success('Configuration updated');
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="max-w-2xl w-full">
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Update configuration</DialogTitle>
            <DialogDescription>
              Updating this configuration will change the behavior of the agent.
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-3 py-4 w-full">
            <Label htmlFor="name">Name</Label>
            <div className="flex flex-col gap-1.5 col-span-3">
              <Input id="name" {...form.register('name')} />
            </div>
          </div>
          <div className="flex flex-col gap-3 py-4 w-full">
            <Label htmlFor="agent_config">Agent config</Label>
            <div className="flex flex-col gap-1.5 w-full">
              <Controller
                control={form.control}
                name="agentConfig"
                render={({ field }) => (
                  <JsonEditor
                    data={field.value}
                    setData={(data) => {
                      console.log(data);
                      field.onChange(data);
                    }}
                    className="w-full"
                  />
                )}
              />
            </div>
          </div>
          <div className="flex flex-col gap-3 py-4 w-full">
            <Label htmlFor="easylogApiKey">Easylog API key</Label>
            <div className="flex flex-col gap-1.5 col-span-3">
              <Input id="easylogApiKey" {...form.register('easylogApiKey')} />
            </div>
          </div>
          <DialogFooter>
            <Button type="submit">Update configuration</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default ConfigurationUpdateDialog;
