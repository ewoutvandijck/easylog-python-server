import { zodResolver } from '@hookform/resolvers/zod';
import { UseFormProps, useForm } from 'react-hook-form';
import { z } from 'zod';

const useZodForm = <TSchema extends z.ZodSchema, TContext = unknown>(
  schema: TSchema,
  props?: UseFormProps<z.infer<TSchema>, TContext>
) => {
  return useForm<z.infer<TSchema>>({
    resolver: zodResolver(schema),
    ...props
  });
};

export default useZodForm;
