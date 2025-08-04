import * as Sentry from '@sentry/nextjs';
import { tool } from 'ai';
import { z } from 'zod';

import tryCatch from '@/utils/try-catch';

import getEasylogClient from './utils/getEasylogClient';

const toolGetResourceGroups = (userId: string) => {
  return tool({
    description:
      'Retrieve individual resources within a specific resource group. Fixes schema mismatch between API response and client.',
    inputSchema: z.object({
      resourceId: z.number().describe('The ID of the resource'),
      resourceSlug: z
        .string()
        .describe('The slug identifier for the resource group')
    }),
    execute: async ({ resourceId, resourceSlug }) => {
      const client = await getEasylogClient(userId);

      const [apiResponse, error] = await tryCatch(
        client.planningResources.v2DatasourcesResourcesResourceIdResourceSlugGet(
          {
            resourceId,
            resourceSlug
          }
        )
      );

      if (error) {
        Sentry.captureException(error);
        return `Error getting resource groups: ${error.message}`;
      }

      console.log('raw API response', apiResponse);

      // 🔧 FIX: Schema mismatch - API retourneert 'items' maar client verwacht 'data'
      // Transform API response van {items: {...}} naar {data: {...}} format
      const resourceGroups = {
        data: (apiResponse as any)?.items || apiResponse?.data || {}
      };

      console.log('transformed resource groups', resourceGroups);

      return JSON.stringify(resourceGroups, null, 2);
    }
  });
};

export default toolGetResourceGroups;
