import { tool } from 'ai';
import { z } from 'zod';

import { PhaseUpdateBody } from '@/lib/easylog/generated-client/models';

import getEasylogClient from './utils/getEasylogClient';

const toolUpdatePlanningPhase = (userId: string) => {
  return tool({
    description: 'Update the date range of an existing planning phase.',
    inputSchema: z.object({
      phaseId: z.number().describe('The ID of the phase to update'),
      start: z
        .string()
        .describe('New start date (accepts various date formats)'),
      end: z.string().describe('New end date (accepts various date formats)')
    }),
    execute: async ({ phaseId, start, end }) => {
      const client = await getEasylogClient(userId);

      const phaseUpdateBody: PhaseUpdateBody = {
        start: new Date(start),
        end: new Date(end)
      };

      await client.planningPhases.v2DatasourcesPhasesPhaseIdPut({
        phaseId,
        phaseUpdateBody
      });

      const phase = await client.planningPhases.v2DatasourcesPhasesPhaseIdGet({
        phaseId
      });
      return JSON.stringify(phase, null, 2);
    }
  });
};

export default toolUpdatePlanningPhase;
