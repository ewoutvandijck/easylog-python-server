import { zodResolver } from '@hookform/resolvers/zod';
import { UseFormProps, useForm } from 'react-hook-form';
import { z } from 'zod';

const useZodForm = <TSchema extends z.Schema, TContext = unknown>(
  schema: TSchema,
  props?: UseFormProps<z.infer<TSchema>, TContext>
) => {
  return useForm<z.infer<TSchema>>({
    resolver: zodResolver<z.infer<TSchema>>(schema),
    ...props
  });
};

export default useZodForm;
