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

      // Method 1: Get headers (first row columns) using header: 1
      const headers = XLSX.utils.sheet_to_json(sheet, {
        header: 1
      })[0] as string[];
      logger.info('Headers', { headers });

      // Method 2: Alternative approach - get first row using range
      const range = XLSX.utils.decode_range(sheet['!ref'] || 'A1');
      const firstRowHeaders: string[] = [];

      for (let col = range.s.c; col <= range.e.c; col++) {
        const cellAddress = XLSX.utils.encode_cell({ r: 0, c: col });
        const cell = sheet[cellAddress];
        firstRowHeaders.push(cell?.v?.toString() || `Column${col + 1}`);
      }

      logger.info('First row headers (alternative method)', {
        firstRowHeaders
      });

      // Get data (excluding header row)
      const json = XLSX.utils.sheet_to_json(sheet);

      return {
        sheetName,
        sheetIndex: index,
        headers,
        firstRowHeaders,
        content: json
      };
    });
  }
});
