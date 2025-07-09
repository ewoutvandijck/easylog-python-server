import { isMacOs } from 'react-device-detect';
import { VariantProps, tv } from 'tailwind-variants';

import useKeyboardShortcut from '../../hooks/useKeyboardShortcut';

export const shortcutStyles = tv({
  base: 'text-text-primary-on-fill/75 inline-flex text-xs tracking-widest'
});

export interface ShortcutProps
  extends VariantProps<typeof shortcutStyles>,
    React.HTMLAttributes<HTMLSpanElement> {
  command: string[];
  callback?: (event: KeyboardEvent) => void;
}

const SPECIAL_KEYS = {
  cmd: '⌘',
  ctrl: '⌃',
  enter: '↵',
  space: '␣',
  backspace: '⌫',
  delete: '⌦'
};

const Shortcut = ({
  className,
  command,
  callback,
  ...props
}: ShortcutProps) => {
  useKeyboardShortcut(command, (e) => {
    callback?.(e);
  });

  return (
    <span className={shortcutStyles({ className })} {...props}>
      {command
        .map((key) =>
          key === 'meta'
            ? isMacOs
              ? '⌘'
              : 'Ctrl'
            : key in SPECIAL_KEYS
              ? SPECIAL_KEYS[key as keyof typeof SPECIAL_KEYS]
              : key
        )
        .join('')}
    </span>
  );
};

export default Shortcut;
