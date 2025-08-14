import * as fs from 'fs';
import path from 'path';

import XLSX from 'xlsx';

import analyzeColumn from '@/jobs/ingest-document/utils/analyzeColumn';

XLSX.set_fs(fs);

const sheetTest = () => {
  const workbook = XLSX.readFile(path.join(__dirname, './sap_test_data.xlsx'), {
    cellDates: true
  });

  const parts = workbook.SheetNames.map((sheetName) => {
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
    );

    return {
      name: sheetName,
      columns: Array.from(new Set(data.flatMap((row) => Object.keys(row)))),
      data
    };
  });

  const analysis = parts.map((part) => {
    return {
      name: part.name,
      analysis: part.columns.map((column) => {
        return analyzeColumn(part.data, column);
      })
    };
  });

  console.dir(analysis, { depth: null });
};

sheetTest();
