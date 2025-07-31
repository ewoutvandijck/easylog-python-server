import { createOpenRouter } from '@openrouter/ai-sdk-provider';

import serverConfig from '@/server.config';

/** @see https://openrouter.ai/models */
const openrouter = createOpenRouter({
  apiKey: serverConfig.openrouterApiKey,
  extraBody: {
    transforms: ['middle-out']
  }
});

export default openrouter;
