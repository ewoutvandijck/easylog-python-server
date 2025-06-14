import { Command as CommandPrimitive } from 'cmdk';
import { VariantProps, tv } from 'tailwind-variants';

export const commandEmptyStyles = tv({
  base: 'py-6 text-center text-sm'
});

export interface CommandEmptyProps
  extends VariantProps<typeof commandEmptyStyles>,
    React.ComponentProps<typeof CommandPrimitive.Empty> {}

const CommandEmpty = ({ children, className, ...props }: CommandEmptyProps) => {
  return (
    <CommandPrimitive.Empty
      className={commandEmptyStyles({ className })}
      {...props}
    >
      {children}
    </CommandPrimitive.Empty>
  );
};

export default CommandEmpty;
