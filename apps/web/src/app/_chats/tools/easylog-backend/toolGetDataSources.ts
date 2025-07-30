import * as Sentry from '@sentry/nextjs';
import { tool } from 'ai';
import { z } from 'zod';

import tryCatch from '@/utils/try-catch';

import getEasylogClient from './utils/getEasylogClient';

const toolGetDataSources = (userId: string) => {
  return tool({
    description: 'Get all datasources from Easylog',
    inputSchema: z.object({
      types: z.array(z.string()).describe('Empty array to get all datasources')
    }),
    execute: async ({ types }) => {
      const client = await getEasylogClient(userId);

      const [datasources, error] = await tryCatch(
        client.datasources.v2DatasourcesGet({
          types
        })
      );

      if (error) {
        Sentry.captureException(error);
        return `Error getting datasources: ${error.message}`;
      }

      console.log('datasources', datasources);

      return JSON.stringify(datasources, null, 2);
    }
  });
};

export default toolGetDataSources;
