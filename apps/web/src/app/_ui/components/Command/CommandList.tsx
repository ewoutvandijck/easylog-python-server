import { Command as CommandPrimitive } from 'cmdk';
import { VariantProps, tv } from 'tailwind-variants';

export const commandListStyles = tv({
  base: 'max-h-[300px]'
});

export interface CommandListProps
  extends VariantProps<typeof commandListStyles>,
    React.ComponentProps<typeof CommandPrimitive.List> {}

const CommandList = ({ children, className, ...props }: CommandListProps) => {
  return (
    <CommandPrimitive.List
      className={commandListStyles({ className })}
      {...props}
    >
      {children}
    </CommandPrimitive.List>
  );
};

export default CommandList;
