import { z } from 'zod';

import serverConfig from '@/server.config';

const agentConfigSchema = z.object({
  model: z
    .string()
    .min(1)
    .optional()
    .default(serverConfig.defaultAgentConfig.model),
  prompt: z
    .string()
    .min(1)
    .optional()
    .default(serverConfig.defaultAgentConfig.prompt),
  reasoning: z.object({
    enabled: z.boolean().optional().default(false),
    effort: z.enum(['high', 'medium', 'low']).optional().default('medium')
  })
});

export type AgentConfig = z.infer<typeof agentConfigSchema>;

export default agentConfigSchema;
