import { createOpenAI } from '@ai-sdk/openai';

import serverConfig from '@/server.config';

/** @see https://openrouter.ai/models */
const openrouter = createOpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: serverConfig.openrouterApiKey,
  fetch: (url, options) => {
    console.log(url, options);
    return fetch(url, {
      ...options,
      body:
        typeof options?.body === 'string'
          ? JSON.stringify(
              {
                ...JSON.parse(options.body),
                transforms: ['middle-out']
              },
              null,
              2
            )
          : options?.body
    });
  }
});

export default openrouter;
