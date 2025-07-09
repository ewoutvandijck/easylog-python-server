import { IconSearch } from '@tabler/icons-react';
import { Command as CommandPrimitive } from 'cmdk';
import { VariantProps, tv } from 'tailwind-variants';

import Icon from '../Icon/Icon';

export const commandInputStyles = tv({
  slots: {
    wrapper: 'border-b-border-muted flex items-center border-b px-3',
    icon: 'mr-2 size-4 shrink-0 opacity-50',
    input:
      'outline-hidden placeholder:text-text-muted flex h-10 w-full rounded-md bg-transparent py-3 text-sm disabled:cursor-not-allowed disabled:opacity-50'
  }
});

const { wrapper, icon, input } = commandInputStyles();

export interface CommandInputProps
  extends VariantProps<typeof commandInputStyles>,
    React.ComponentProps<typeof CommandPrimitive.Input> {}

const CommandInput = ({ ref, className, ...props }: CommandInputProps) => {
  return (
    <div className={wrapper()} cmdk-input-wrapper="">
      <Icon icon={IconSearch} className={icon()} />
      <CommandPrimitive.Input
        ref={ref}
        className={input({ className })}
        {...props}
      />
    </div>
  );
};

export default CommandInput;
