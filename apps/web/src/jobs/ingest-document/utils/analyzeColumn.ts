type BaseColumnAnalysis = {
  columnName: string;
};

type DateColumnAnalysis = BaseColumnAnalysis & {
  columnType: 'date';
  min: Date;
  max: Date;
  sampleValues: Date[];
  uniqueValues: number;
  emptyValues: number;
};

type NumberColumnAnalysis = BaseColumnAnalysis & {
  columnType: 'number';
  min: number;
  max: number;
  sampleValues: number[];
  uniqueValues: number;
  emptyValues: number;
};

type BooleanColumnAnalysis = BaseColumnAnalysis & {
  columnType: 'boolean';
  trueValues: number;
  falseValues: number;
  emptyValues: number;
};

type StringColumnAnalysis = BaseColumnAnalysis & {
  columnType: 'string';
  sampleValues: string[];
  uniqueValues: number;
  emptyValues: number;
};

type ColumnAnalysis =
  | DateColumnAnalysis
  | NumberColumnAnalysis
  | BooleanColumnAnalysis
  | StringColumnAnalysis;

const analyzeColumn = (
  records: Record<string, string | number | boolean | null | undefined>[],
  columnName: string
): ColumnAnalysis => {
  const columnValues = records.map((record) => record[columnName]);

  const uniqueValues = [...new Set(columnValues)];
};

export default analyzeColumn;
