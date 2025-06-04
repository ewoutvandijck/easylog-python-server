import { type VariantProps, tv } from 'tailwind-variants';

export const sidebarFooterStyles = tv({
  base: 'flex flex-col gap-1'
});

export interface SidebarFooterProps
  extends VariantProps<typeof sidebarFooterStyles>,
    React.HTMLAttributes<HTMLDivElement> {}

const SidebarFooter = ({
  children,
  className,
  ...props
}: React.PropsWithChildren<SidebarFooterProps>) => {
  return (
    <div className={sidebarFooterStyles({ className })} {...props}>
      {children}
    </div>
  );
};

export default SidebarFooter;
