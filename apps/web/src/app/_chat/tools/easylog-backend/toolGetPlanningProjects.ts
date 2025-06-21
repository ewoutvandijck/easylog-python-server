import * as Sentry from '@sentry/nextjs';
import { tool } from 'ai';
import { z } from 'zod';

import tryCatch from '@/utils/try-catch';

import getEasylogClient from './utils/getEasylogClient';

const toolGetPlanningProjects = (userId: string) => {
  return tool({
    description:
      'Retrieve all planning projects available for allocation within a date range.',
    inputSchema: z.object({
      startDate: z
        .string()
        .nullable()
        .describe('Optional start date in YYYY-MM-DD format'),
      endDate: z
        .string()
        .nullable()
        .describe('Optional end date in YYYY-MM-DD format')
    }),
    execute: async ({ startDate, endDate }) => {
      const client = await getEasylogClient(userId);

      const [projects, error] = await tryCatch(
        client.planning.v2DatasourcesProjectsGet({
          startDate: startDate ? new Date(startDate) : undefined,
          endDate: endDate ? new Date(endDate) : undefined
        })
      );

      if (error) {
        Sentry.captureException(error);
        return `Error getting projects: ${error.message}`;
      }

      return JSON.stringify(projects, null, 2);
    }
  });
};

export default toolGetPlanningProjects;
