/**
 * Splits an array into batches of a specified size.
 *
 * @param array - The array to split into batches.
 * @param batchSize - The size of each batch.
 * @returns An array of batches, where each batch is an array of elements.
 */
const splitArrayBatches = <T>(array: T[], batchSize: number) => {
  const batches: T[][] = [];

  for (let i = 0; i < array.length; i += batchSize) {
    batches.push(array.slice(i, i + batchSize));
  }

  return batches;
};

export default splitArrayBatches;
