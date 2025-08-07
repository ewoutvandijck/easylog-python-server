import * as Sentry from '@sentry/nextjs';
import { tool } from 'ai';
import { z } from 'zod';

import {
  AdditionalAllocationData,
  DatasourceAllocationMultipleUpdateBody
} from '@/lib/easylog/generated-client/models';
import tryCatch from '@/utils/try-catch';

import getEasylogClient from './utils/getEasylogClient';

const resourceAllocationUpdateSchema = z.object({
  id: z.number().describe('ID of the existing allocation to update'),
  start: z.string().describe('Start date/time of the allocation'),
  end: z.string().describe('End date/time of the allocation'),
  type: z
    .string()
    .nullable()
    .optional()
    .describe(
      'Allocation type (e.g., "modificatiesi"). If omitted, will not be updated'
    ),
  comment: z
    .string()
    .nullable()
    .optional()
    .describe(
      'Optional comment for the allocation. If omitted, will not be updated'
    ),
  parentId: z
    .number()
    .nullable()
    .optional()
    .describe('Parent allocation ID. If omitted, will not be updated'),
  fields: z
    .array(
      z
        .object({})
        .catchall(z.union([z.number(), z.string()]))
        .strict()
    )
    .nullable()
    .optional()
    .describe('Optional additional fields. If omitted, will not be updated')
});

const toolUpdateMultipleAllocations = (userId: string) => {
  return tool({
    description:
      'Update multiple existing resource allocations in a single operation. Only the fields provided will be updated.',
    inputSchema: z.object({
      allocations: z
        .array(resourceAllocationUpdateSchema)
        .describe(
          'List of allocation updates. Each allocation must include an ID and the fields to update'
        )
    }),
    execute: async ({ allocations }) => {
      const client = await getEasylogClient(userId);

      const datasourceAllocationMultipleUpdateBody: DatasourceAllocationMultipleUpdateBody =
        {
          allocations: allocations.map((allocation) => ({
            id: allocation.id,
            start: new Date(allocation.start),
            end: new Date(allocation.end),
            ...(allocation.type !== undefined && { type: allocation.type }),
            ...(allocation.comment !== undefined && {
              comment: allocation.comment
            }),
            ...(allocation.parentId !== undefined && {
              parentId: allocation.parentId
            }),
            ...(allocation.fields !== undefined && {
              fields: allocation.fields as AdditionalAllocationData[]
            })
          }))
        };

      const [updatedAllocations, error] = await tryCatch(
        client.allocations.v2DatasourcesAllocationsMultiplePut({
          datasourceAllocationMultipleUpdateBody
        })
      );

      if (error) {
        Sentry.captureException(error);
        return `Error updating allocations: ${error.message}`;
      }

      console.log('Updated allocations:', updatedAllocations);

      return JSON.stringify(updatedAllocations, null, 2);
    }
  });
};

export default toolUpdateMultipleAllocations;
