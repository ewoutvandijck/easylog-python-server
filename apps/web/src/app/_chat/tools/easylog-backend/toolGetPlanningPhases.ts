import * as Sentry from '@sentry/nextjs';
import { tool } from 'ai';
import { z } from 'zod';

import tryCatch from '@/utils/try-catch';

import getEasylogClient from './utils/getEasylogClient';

const toolGetPlanningPhases = (userId: string) => {
  return tool({
    description: 'Retrieve all planning phases for a specific project.',
    inputSchema: z.object({
      projectId: z.number().describe('The ID of the project to get phases for')
    }),
    execute: async ({ projectId }) => {
      const client = await getEasylogClient(userId);

      const [phases, error] = await tryCatch(
        client.planningPhases.v2DatasourcesProjectProjectIdPhasesGet({
          projectId
        })
      );

      if (error) {
        Sentry.captureException(error);
        return `Error getting phases: ${error.message}`;
      }

      return JSON.stringify(phases, null, 2);
    }
  });
};

export default toolGetPlanningPhases;
