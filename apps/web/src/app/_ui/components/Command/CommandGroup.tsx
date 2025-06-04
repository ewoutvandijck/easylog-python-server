import { Command as CommandPrimitive } from 'cmdk';
import { VariantProps, tv } from 'tailwind-variants';

export const commandGroupStyles = tv({
  base: 'p-1 text-text-primary [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-text-muted'
});

export interface CommandGroupProps
  extends VariantProps<typeof commandGroupStyles>,
    React.ComponentProps<typeof CommandPrimitive.Group> {}

const CommandGroup = ({ children, className, ...props }: CommandGroupProps) => {
  return (
    <CommandPrimitive.Group
      className={commandGroupStyles({ className })}
      {...props}
    >
      {children}
    </CommandPrimitive.Group>
  );
};

export default CommandGroup;
