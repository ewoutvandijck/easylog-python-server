import { z } from 'zod';
import { messageContentSchema } from './message-contents';

export const messageSchema = z.object({
  role: z.enum(['user', 'assistant', 'system', 'developer']),
  contents: z.array(messageContentSchema)
});

export type Message = z.infer<typeof messageSchema>;
