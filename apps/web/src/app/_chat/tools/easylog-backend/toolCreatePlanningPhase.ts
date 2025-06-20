import { tool } from 'ai';
import { z } from 'zod';

import { PhaseBody } from '@/lib/easylog/generated-client/models';

import getEasylogClient from './utils/getEasylogClient';

const toolCreatePlanningPhase = (userId: string) => {
  return tool({
    description: 'Create a new planning phase for a project.',
    inputSchema: z.object({
      projectId: z
        .number()
        .describe('The ID of the project to create a phase for'),
      slug: z
        .string()
        .describe(
          'Identifier slug for the phase (e.g., "design", "development")'
        ),
      start: z
        .string()
        .describe('Start date for the phase (accepts various date formats)'),
      end: z
        .string()
        .describe('End date for the phase (accepts various date formats)')
    }),
    execute: async ({ projectId, slug, start, end }) => {
      const client = await getEasylogClient(userId);

      const phaseBody: PhaseBody = {
        slug,
        start: new Date(start),
        end: new Date(end)
      };

      const phase =
        await client.planningPhases.v2DatasourcesProjectProjectIdPhasesPost({
          projectId,
          phaseBody
        });
      return JSON.stringify(phase, null, 2);
    }
  });
};

export default toolCreatePlanningPhase;
