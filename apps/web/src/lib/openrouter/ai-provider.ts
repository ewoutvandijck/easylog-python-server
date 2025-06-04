import { createOpenRouter } from '@openrouter/ai-sdk-provider';

import serverConfig from '@/server.config';

const openrouterProvider = createOpenRouter({
  apiKey: serverConfig.openrouterApiKey
});

export default openrouterProvider;
