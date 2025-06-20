import { tool } from 'ai';
import { z } from 'zod';

import getEasylogClient from './utils/getEasylogClient';

const toolGetResourceGroups = (userId: string) => {
  return tool({
    description:
      'Retrieve all resource groups for a specific resource and group slug.',
    inputSchema: z.object({
      resourceId: z.number().describe('The ID of the resource'),
      resourceSlug: z
        .string()
        .describe('The slug identifier for the resource group')
    }),
    execute: async ({ resourceId, resourceSlug }) => {
      const client = await getEasylogClient(userId);

      const resourceGroups =
        await client.planningResources.v2DatasourcesResourcesResourceIdResourceSlugGet(
          {
            resourceId,
            resourceSlug
          }
        );

      return JSON.stringify(resourceGroups, null, 2);
    }
  });
};

export default toolGetResourceGroups;
