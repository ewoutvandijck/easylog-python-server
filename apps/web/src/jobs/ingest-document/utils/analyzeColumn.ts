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

  const nonEmptyValues = columnValues.filter(
    (value) => value !== null && value !== undefined && value !== ''
  );

  if (nonEmptyValues.length === 0) {
    return {
      columnName,
      columnType: 'string',
      sampleValues: [],
      uniqueValues: 0,
      emptyValues: columnValues.length
    } as StringColumnAnalysis;
  }

  const uniqueValues = [...new Set(nonEmptyValues)];

  const emptyValues = columnValues.length - nonEmptyValues.length;

  const isDate = (value: unknown): value is Date => {
    if (value instanceof Date && !isNaN(value.getTime())) return true;
    return false;
  };

  let columnType: 'date' | 'number' | 'boolean' | 'string';

  if (uniqueValues.every(isDate)) {
    columnType = 'date';
  } else if (uniqueValues.every((value) => typeof value === 'number')) {
    columnType = 'number';
  } else if (uniqueValues.every((value) => typeof value === 'boolean')) {
    columnType = 'boolean';
  } else {
    columnType = 'string';
  }

  if (columnType === 'date') {
    const min = new Date(
      Math.min(
        ...nonEmptyValues.map((value) => (value as unknown as Date).getTime())
      )
    );
    const max = new Date(
      Math.max(
        ...nonEmptyValues.map((value) => (value as unknown as Date).getTime())
      )
    );

    const sampleValues = uniqueValues.slice(0, 5) as unknown as Date[];

    return {
      columnName,
      columnType,
      min,
      max,
      sampleValues,
      uniqueValues: uniqueValues.length,
      emptyValues
    } as DateColumnAnalysis;
  }

  if (columnType === 'number') {
    const min = Math.min(...nonEmptyValues.map((value) => value as number));
    const max = Math.max(...nonEmptyValues.map((value) => value as number));

    const sampleValues = uniqueValues.slice(0, 5) as unknown as number[];

    return {
      columnName,
      columnType,
      min,
      max,
      sampleValues,
      uniqueValues: uniqueValues.length,
      emptyValues
    } as NumberColumnAnalysis;
  }

  if (columnType === 'boolean') {
    const trueValues = nonEmptyValues.filter((value) => value === true).length;
    const falseValues = nonEmptyValues.filter(
      (value) => value === false
    ).length;

    return {
      columnName,
      columnType,
      trueValues,
      falseValues,
      emptyValues
    } as BooleanColumnAnalysis;
  }

  return {
    columnName,
    columnType,
    sampleValues: (uniqueValues.slice(0, 5) as unknown as string[]).map(
      (value) => value.slice(0, 255)
    ),
    uniqueValues: uniqueValues.length,
    emptyValues
  } as StringColumnAnalysis;
};

export default analyzeColumn;
