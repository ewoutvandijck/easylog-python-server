import { tool } from 'ai';
import { z } from 'zod';

import getEasylogClient from './utils/getEasylogClient';

const toolGetResources = (userId: string) => {
  return tool({
    description: 'Retrieve all available resources in the system.',
    inputSchema: z.object({}),
    execute: async () => {
      const client = await getEasylogClient(userId);
      const resources =
        await client.planningResources.v2DatasourcesResourcesGet();
      return JSON.stringify(resources, null, 2);
    }
  });
};

export default toolGetResources;
