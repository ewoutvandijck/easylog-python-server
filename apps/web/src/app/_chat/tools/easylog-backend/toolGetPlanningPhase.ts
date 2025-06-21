import { tool } from 'ai';
import { z } from 'zod';

import tryCatch from '@/utils/try-catch';

import getEasylogClient from './utils/getEasylogClient';

const toolGetPlanningPhase = (userId: string) => {
  return tool({
    description:
      'Retrieve detailed information about a specific planning phase.',
    inputSchema: z.object({
      phaseId: z.number().describe('The ID of the planning phase to retrieve')
    }),
    execute: async ({ phaseId }) => {
      const client = await getEasylogClient(userId);

      const [phase, error] = await tryCatch(
        client.planningPhases.v2DatasourcesPhasesPhaseIdGet({
          phaseId
        })
      );

      if (error) {
        return `Error getting phase: ${error.message}`;
      }
      return JSON.stringify(phase, null, 2);
    }
  });
};

export default toolGetPlanningPhase;
