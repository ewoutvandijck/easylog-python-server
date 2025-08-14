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
    const workbook = XLSX.read(buffer, { type: 'buffer', cellDates: true });

    return workbook.SheetNames.map((sheetName) => {
      const sheet = workbook.Sheets[sheetName];

      const rawData = XLSX.utils.sheet_to_json(sheet) as Record<
        string,
        string | number | boolean | null | undefined
      >[];

      const data = rawData.map((row) =>
        Object.fromEntries(
          Object.entries(row).map(([key, value]) => {
            if (typeof value === 'string') {
              const trimmed = value.trim();
              return [key, trimmed === '' ? null : trimmed];
            }

            return [key, value];
          })
        )
      ) as Record<string, string | number | boolean | null | undefined>[];

      return {
        name: sheetName,
        columns: Array.from(new Set(data.flatMap((row) => Object.keys(row)))),
        data
      };
    });
  }
});
