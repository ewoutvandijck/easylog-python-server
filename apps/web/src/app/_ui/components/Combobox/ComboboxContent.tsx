import { tv } from 'tailwind-variants';

import Command from '../Command/Command';
import PopoverContent, { PopoverContentProps } from '../Popover/PopoverContent';

export const comboboxContentStyles = tv({
  base: 'min-w-[var(--radix-popover-trigger-width)] p-0'
});

export interface ComboboxContentProps extends PopoverContentProps {}

const ComboboxContent = ({
  className,
  children,
  ...props
}: ComboboxContentProps) => {
  return (
    <PopoverContent
      className={comboboxContentStyles({ className })}
      align="start"
      {...props}
    >
      <Command shouldFilter={false}>{children}</Command>
    </PopoverContent>
  );
};

export default ComboboxContent;
