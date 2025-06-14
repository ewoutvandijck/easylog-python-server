/**
 * A higher order function that takes a function, executes it and returns its
 * value. If the function throws an error, it will be returned as the second
 * element of the tuple.
 *
 * @param promise - The promise to execute
 * @returns A tuple of [value, error]
 */
const tryCatch = async <T, E = Error | DOMException>(promise: Promise<T>) => {
  try {
    return [await promise, undefined] as const;
  } catch (error) {
    return [undefined, error as E] as const;
  }
};

export default tryCatch;
