import * as fs from 'fs';

import { logger, schemaTask } from '@trigger.dev/sdk';
import * as XLSX from 'xlsx';
import { z } from 'zod';

import splitArrayBatches from '@/utils/split-array-batches';

/* load 'fs' for readFile and writeFile support */
XLSX.set_fs(fs);

export const processXlsxJob = schemaTask({
  id: 'process-xlsx',
  schema: z.object({
    downloadUrl: z.string(),
    chunkSize: z.number().optional().default(5000)
  }),
  run: async ({ downloadUrl, chunkSize }) => {
    logger.info('Document URL', { downloadUrl });

    const response = await fetch(downloadUrl);
    const buffer = await response.arrayBuffer();
    const workbook = XLSX.read(buffer, { type: 'buffer' });

    return workbook.SheetNames.flatMap((sheetName, sheetIndex) => {
      logger.info('Sheet name', { sheetName });

      const sheet = workbook.Sheets[sheetName];
      const json = XLSX.utils.sheet_to_json(sheet);

      const averageRowSize =
        json.reduce<number>((acc, row) => acc + JSON.stringify(row).length, 0) /
        json.length;

      logger.info('Average row size', {
        averageRowSize,
        jsonLength: json.length,
        sheetName
      });

      const chunks = splitArrayBatches(
        json,
        Math.floor(chunkSize / averageRowSize)
      );

      logger.info('Chunks', {
        chunksLength: chunks.length,
        chunks
      });

      const parts = chunks.map((chunk, index) => ({
        sheetName,
        sheetIndex,
        content: chunk,
        order: index
      }));

      return parts;
    });
  }
});
