import { tool } from 'ai';
import { z } from 'zod';

import getEasylogClient from './utils/getEasylogClient';

const toolGetPlanningPhases = (userId: string) => {
  return tool({
    description: 'Retrieve all planning phases for a specific project.',
    inputSchema: z.object({
      projectId: z.number().describe('The ID of the project to get phases for')
    }),
    execute: async ({ projectId }) => {
      const client = await getEasylogClient(userId);
      const phases =
        await client.planningPhases.v2DatasourcesProjectProjectIdPhasesGet({
          projectId
        });
      return JSON.stringify(phases, null, 2);
    }
  });
};

export default toolGetPlanningPhases;
