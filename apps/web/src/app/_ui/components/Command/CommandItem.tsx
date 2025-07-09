import { Command as CommandPrimitive } from 'cmdk';
import { VariantProps, tv } from 'tailwind-variants';

export const commandItemStyles = tv({
  base: 'outline-hidden relative flex min-h-10 cursor-default select-none items-center rounded-lg px-2.5 py-1.5 text-sm hover:bg-fill-muted data-[disabled=true]:pointer-events-none data-[selected=true]:bg-fill-muted data-[selected=true]:text-text-primary data-[disabled=true]:opacity-50'
});

export interface CommandItemProps
  extends VariantProps<typeof commandItemStyles>,
    React.ComponentProps<typeof CommandPrimitive.Item> {}

const CommandItem = ({ children, className, ...props }: CommandItemProps) => {
  return (
    <CommandPrimitive.Item
      className={commandItemStyles({ className })}
      {...props}
    >
      {children}
    </CommandPrimitive.Item>
  );
};

export default CommandItem;
