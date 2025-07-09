import * as fs from 'fs';

import { logger, schemaTask } from '@trigger.dev/sdk';
import * as XLSX from 'xlsx';
import { z } from 'zod';

/* load 'fs' for readFile and writeFile support */
XLSX.set_fs(fs);

export const processXlsxJob = schemaTask({
  id: 'process-xlsx',
  schema: z.object({
    downloadUrl: z.string()
  }),
  run: async ({ downloadUrl }) => {
    logger.info('Document URL', { downloadUrl });

    const response = await fetch(downloadUrl);
    const buffer = await response.arrayBuffer();
    const workbook = XLSX.read(buffer, { type: 'buffer' });

    return workbook.SheetNames.map((sheetName, index) => {
      logger.info('Sheet name', { sheetName });

      const sheet = workbook.Sheets[sheetName];
      const json = XLSX.utils.sheet_to_json(sheet);

      return {
        sheetName,
        sheetIndex: index,
        content: json
      };
    });
  }
});
