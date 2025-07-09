import { tool } from 'ai';
import { z } from 'zod';

import tryCatch from '@/utils/try-catch';

const toolExecuteSQL = () => {
  return tool({
    description: 'Execute a SQL query on the Easylog database',
    inputSchema: z.object({
      query: z.string()
    }),
    execute: async (query) => {
      const [importData, importError] = await tryCatch(
        import('@/lib/easylog/db')
      );

      if (importError) {
        return `Error importing Easylog database: ${importError.message}`;
      }

      const { default: easylogDb } = importData;

      const [result, error] = await tryCatch(easylogDb.execute(query.query));

      if (error) {
        return `Error executing SQL query: ${error.message}`;
      }

      return JSON.stringify(result, null, 2);
    }
  });
};

export default toolExecuteSQL;
