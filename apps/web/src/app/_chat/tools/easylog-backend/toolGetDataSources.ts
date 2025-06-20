import { tool } from 'ai';
import { z } from 'zod';

import getEasylogClient from './utils/getEasylogClient';

const toolGetDataSources = (userId: string) => {
  return tool({
    description: 'Get all datasources from Easylog',
    inputSchema: z.object({
      types: z.array(z.string()).describe('Empty array to get all datasources')
    }),
    execute: async ({ types }) => {
      const client = await getEasylogClient(userId);

      const datasources = await client.datasources.v2DatasourcesGet({
        types
      });

      return JSON.stringify(datasources, null, 2);
    }
  });
};

export default toolGetDataSources;
