import { tool } from 'ai';
import { z } from 'zod';

import getEasylogClient from './utils/getEasylogClient';

const toolGetPlanningProject = (userId: string) => {
  return tool({
    description:
      'Retrieve detailed information about a specific planning project.',
    inputSchema: z.object({
      projectId: z
        .number()
        .describe('The ID of the planning project to retrieve')
    }),
    execute: async ({ projectId }) => {
      const client = await getEasylogClient(userId);

      const project = await client.planning.v2DatasourcesProjectsProjectIdGet({
        projectId
      });

      return JSON.stringify(project, null, 2);
    }
  });
};

export default toolGetPlanningProject;
