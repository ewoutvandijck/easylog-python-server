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
    .default(serverConfig.defaultAgentConfig.prompt)
});

export type AgentConfig = z.infer<typeof agentConfigSchema>;

export default agentConfigSchema;
