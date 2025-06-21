import * as Sentry from '@sentry/nextjs';
import { tool } from 'ai';
import { z } from 'zod';

import tryCatch from '@/utils/try-catch';

import getEasylogClient from './utils/getEasylogClient';

const toolDeleteAllocation = (userId: string) => {
  return tool({
    description: 'Delete an allocation',
    inputSchema: z.object({
      allocationId: z.number().describe('The ID of the allocation to delete')
    }),
    execute: async ({ allocationId }) => {
      const client = await getEasylogClient(userId);

      const [allocations, error] = await tryCatch(
        client.allocations.v2DatasourcesAllocationsAllocationIdDelete({
          allocationId
        })
      );

      if (error) {
        Sentry.captureException(error);
        return `Error getting allocations: ${error.message}`;
      }

      console.log('allocations', allocations);

      return JSON.stringify(allocations, null, 2);
    }
  });
};

export default toolDeleteAllocation;
