import * as Sentry from '@sentry/nextjs';
import { tool } from 'ai';
import { z } from 'zod';

import tryCatch from '@/utils/try-catch';

import getEasylogClient from './utils/getEasylogClient';

const toolGetResources = (userId: string) => {
  return tool({
    description: 'Retrieve all available resources in the system.',
    inputSchema: z.object({}),
    execute: async () => {
      const client = await getEasylogClient(userId);

      const [resources, error] = await tryCatch(
        client.planningResources.v2DatasourcesResourcesGet()
      );

      if (error) {
        Sentry.captureException(error);
        return `Error getting resources: ${error.message}`;
      }

      return JSON.stringify(resources, null, 2);
    }
  });
};

export default toolGetResources;
