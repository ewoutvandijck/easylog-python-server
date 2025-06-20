import { tool } from 'ai';
import { z } from 'zod';

import { ProjectBody } from '@/lib/easylog/generated-client/models';

import getEasylogClient from './utils/getEasylogClient';

const toolUpdatePlanningProject = (userId: string) => {
  return tool({
    description: 'Update properties of an existing planning project.',
    inputSchema: z.object({
      projectId: z.number().describe('The ID of the project to update'),
      name: z.string().nullable().describe('Optional new name for the project'),
      color: z
        .string()
        .nullable()
        .describe('Optional new color code for the project'),
      reportVisible: z
        .boolean()
        .nullable()
        .describe('Optional flag to control report visibility'),
      excludeInWorkdays: z
        .boolean()
        .nullable()
        .describe('Optional flag to exclude project in workday calculations'),
      start: z
        .string()
        .nullable()
        .describe('Optional new start date in YYYY-MM-DD format'),
      end: z
        .string()
        .nullable()
        .describe('Optional new end date in YYYY-MM-DD format'),
      extraData: z
        .object({})
        .catchall(z.union([z.number(), z.string()]))
        .strict()
        .nullable()
        .describe('Optional additional data as a dictionary or JSON string')
    }),
    execute: async ({ projectId, ...updateData }) => {
      const client = await getEasylogClient(userId);

      const projectBody = {
        ...updateData,
        ...(updateData.start && { start: new Date(updateData.start) }),
        ...(updateData.end && { end: new Date(updateData.end) })
      };

      await client.planning.v2DatasourcesProjectsProjectIdPut({
        projectId,
        projectBody: projectBody as ProjectBody
      });

      const project = await client.planning.v2DatasourcesProjectsProjectIdGet({
        projectId
      });
      return JSON.stringify(project, null, 2);
    }
  });
};

export default toolUpdatePlanningProject;
