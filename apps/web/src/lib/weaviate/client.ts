import weaviate, { WeaviateClient } from 'weaviate-client';

import serverConfig from '@/server.config';

let client: WeaviateClient | null = null;

const getWeaviateClient = async () => {
  if (client) return client;

  client = await weaviate.connectToLocal({
    headers: {
      'X-OpenAI-Api-Key': serverConfig.openaiApiKey
    }
  });

  return client;
};

export default getWeaviateClient;
