import * as Sentry from '@sentry/nextjs';
import { tool } from 'ai';
import { z } from 'zod';

import tryCatch from '@/utils/try-catch';

import getEasylogClient from './utils/getEasylogClient';

const toolGetProjectsOfResource = (userId: string) => {
  return tool({
    description:
      'Retrieve all projects associated with a specific resource and allocation type.',
    inputSchema: z.object({
      resourceId: z.number().describe('The ID of the resource group'),
      datasourceSlug: z
        .string()
        .describe(
          'The slug of the allocation type (e.g., "td", "modificaties")'
        )
    }),
    execute: async ({ resourceId, datasourceSlug }) => {
      const client = await getEasylogClient(userId);

      const [projects, error] = await tryCatch(
        client.planningResources.v2DatasourcesResourcesResourceIdProjectsDatasourceSlugGet(
          {
            resourceId,
            datasourceSlug
          }
        )
      );

      if (error) {
        Sentry.captureException(error);
        return `Error getting projects: ${error.message}`;
      }

      return JSON.stringify(projects, null, 2);
    }
  });
};

export default toolGetProjectsOfResource;
