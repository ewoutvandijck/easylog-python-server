import * as Sentry from '@sentry/nextjs';
import { tool } from 'ai';
import { z } from 'zod';

import {
  AdditionalAllocationData,
  DatasourceAllocationMultipleBody
} from '@/lib/easylog/generated-client/models';
import tryCatch from '@/utils/try-catch';

import getEasylogClient from './utils/getEasylogClient';

const resourceAllocationSchema = z.object({
  resourceId: z.number().describe('ID of the resource to allocate'),
  start: z.string().describe('Start date/time of the allocation'),
  end: z.string().describe('End date/time of the allocation'),
  type: z.string().describe('Allocation type (e.g., "modificatiesi")'),
  comment: z
    .string()
    .nullable()
    .describe('Optional comment for the allocation'),
  fields: z
    .array(
      z
        .object({})
        .catchall(z.union([z.number(), z.string()]))
        .strict()
    )
    .describe('Optional additional fields')
});

const toolCreateMultipleAllocations = (userId: string) => {
  return tool({
    description:
      'Allocate multiple resources to a project in a single operation.',
    inputSchema: z.object({
      projectId: z
        .number()
        .describe('The ID of the project to allocate resources to'),
      group: z
        .string()
        .describe('The name of the resource group to allocate to (e.g., "td")'),
      resources: z
        .array(resourceAllocationSchema)
        .describe('List of resource allocation specifications')
    }),
    execute: async ({ projectId, group, resources }) => {
      const client = await getEasylogClient(userId);

      const datasourceAllocationMultipleBody: DatasourceAllocationMultipleBody =
        {
          projectId,
          group,
          resources: resources.map((r) => ({
            ...r,
            start: new Date(r.start),
            end: new Date(r.end),
            fields: r.fields as AdditionalAllocationData[]
          }))
        };

      const [allocations, error] = await tryCatch(
        client.allocations.v2DatasourcesAllocationsMultiplePost({
          datasourceAllocationMultipleBody
        })
      );

      if (error) {
        Sentry.captureException(error);
        return `Error creating allocations: ${error.message}`;
      }

      console.log('allocations', allocations);

      return JSON.stringify(allocations, null, 2);
    }
  });
};

export default toolCreateMultipleAllocations;
