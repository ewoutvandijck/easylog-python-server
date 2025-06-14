import { Command as CommandPrimitive } from 'cmdk';
import { VariantProps, tv } from 'tailwind-variants';

export const commandStyles = tv({
  base: 'text-text-primary flex size-full flex-col rounded-md'
});

export interface CommandProps
  extends VariantProps<typeof commandStyles>,
    React.ComponentProps<typeof CommandPrimitive> {}

const Command = ({ children, className, ...props }: CommandProps) => {
  return (
    <CommandPrimitive {...props} className={commandStyles({ className })}>
      {children}
    </CommandPrimitive>
  );
};

export default Command;
