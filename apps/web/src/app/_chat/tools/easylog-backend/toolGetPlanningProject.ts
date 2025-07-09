import * as Sentry from '@sentry/nextjs';
import { tool } from 'ai';
import { z } from 'zod';

import tryCatch from '@/utils/try-catch';

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

      const [project, error] = await tryCatch(
        client.planning.v2DatasourcesProjectsProjectIdGet({
          projectId
        })
      );

      if (error) {
        Sentry.captureException(error);
        return `Error getting project: ${error.message}`;
      }

      console.log('planning project', project);

      return JSON.stringify(project, null, 2);
    }
  });
};

export default toolGetPlanningProject;
