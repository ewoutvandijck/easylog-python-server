import { tool } from 'ai';
import { z } from 'zod';

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

      const projects =
        await client.planningResources.v2DatasourcesResourcesResourceIdProjectsDatasourceSlugGet(
          {
            resourceId,
            datasourceSlug
          }
        );

      return JSON.stringify(projects, null, 2);
    }
  });
};

export default toolGetProjectsOfResource;
