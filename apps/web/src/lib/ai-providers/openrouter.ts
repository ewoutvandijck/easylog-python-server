import { createOpenAI } from '@ai-sdk/openai';

import serverConfig from '@/server.config';

/** @see https://openrouter.ai/models */
const openrouter = createOpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: serverConfig.openrouterApiKey
});

export default openrouter;
