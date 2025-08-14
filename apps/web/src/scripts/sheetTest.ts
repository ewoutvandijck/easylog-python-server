import * as fs from 'fs';
import path from 'path';

import XLSX from 'xlsx';

import analyzeColumn from '@/jobs/ingest-document/utils/analyzeColumn';

XLSX.set_fs(fs);

const sheetTest = () => {
  const workbook = XLSX.readFile(path.join(__dirname, './sap_test_data.xlsx'), {
    cellDates: true
  });

  workbook.SheetNames.forEach((sheetName) => {
    const sheet = workbook.Sheets[sheetName];

    const data = XLSX.utils.sheet_to_json(sheet) as Record<
      string,
      string | number | boolean | null | undefined
    >[];

    const cleanedData = data.map((row) =>
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

    console.log(analyzeColumn(cleanedData, 'Start'));
  });
};

sheetTest();
