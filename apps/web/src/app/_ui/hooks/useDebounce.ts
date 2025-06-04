import { useEffect, useState } from 'react';

const useDebounce = <Value>(
  value: Value,
  timeoutMs = 500,
  onDebounce?: (value: Value) => void
) => {
  const [debouncedValue, setDebouncedValue] = useState(value);
  const [isDebouncing, setIsDebouncing] = useState(false);

  useEffect(() => {
    setIsDebouncing(true);

    const timeout = setTimeout(() => {
      if (value === debouncedValue) {
        setIsDebouncing(false);
        return;
      }

      setDebouncedValue(value);
      onDebounce?.(value);
      setIsDebouncing(false);
    }, timeoutMs);

    return () => clearTimeout(timeout);
  }, [value, timeoutMs, onDebounce, debouncedValue]);

  return [debouncedValue, isDebouncing] as const;
};

export default useDebounce;
