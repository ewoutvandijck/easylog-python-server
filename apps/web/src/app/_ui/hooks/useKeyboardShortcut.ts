import { useCallback, useEffect, useMemo } from 'react';

const useKeyboardShortcut = (
  command: string[],
  eventCallback: (event: KeyboardEvent) => void
) => {
  const normalized = useMemo(
    () => command.map((c) => c.toLowerCase()),
    [command]
  );

  const down = useCallback(
    (e: KeyboardEvent) => {
      const keyHit = normalized.every((key) => {
        if (key === 'meta') {
          return e.metaKey;
        }

        if (key === 'ctrl') {
          return e.ctrlKey;
        }

        if (key === 'shift') {
          return e.shiftKey;
        }

        if (key === 'alt') {
          return e.altKey;
        }

        return e.key.toLowerCase() === key;
      });

      if (!keyHit) return;

      e.preventDefault();
      eventCallback?.(e);
    },
    [normalized, eventCallback]
  );

  useEffect(() => {
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, [down]);

  return normalized;
};

export default useKeyboardShortcut;
