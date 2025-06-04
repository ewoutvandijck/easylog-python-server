import { VariantProps, tv } from 'tailwind-variants';

export const commandShortcutStyles = tv({
  base: 'text-text-muted ml-auto text-xs tracking-widest'
});

export interface CommandShortcutProps
  extends VariantProps<typeof commandShortcutStyles>,
    React.HTMLAttributes<HTMLSpanElement> {}

const CommandShortcut = ({ className, ...props }: CommandShortcutProps) => {
  return <span className={commandShortcutStyles({ className })} {...props} />;
};

export default CommandShortcut;
