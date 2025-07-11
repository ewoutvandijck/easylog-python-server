import * as Sentry from '@sentry/nextjs';
import { tool } from 'ai';
import { z } from 'zod';

import easylogDb from '@/lib/easylog/db';
import tryCatch from '@/utils/try-catch';

const toolExecuteSQL = () => {
  return tool({
    description: 'Execute a SQL query on the Easylog database',
    inputSchema: z.object({
      query: z.string()
    }),
    execute: async (query) => {
      const [result, error] = await tryCatch(easylogDb.execute(query.query));

      if (error) {
        Sentry.captureException(error);
        console.error(error);
        return `Error executing SQL query: ${error.message}`;
      }

      return JSON.stringify(result, null, 2);
    }
  });
};

export default toolExecuteSQL;
