import { type VariantProps, tv } from 'tailwind-variants';

export const sidebarBodyStyles = tv({
  base: 'flex w-full grow flex-col gap-1 overflow-y-auto'
});

export interface SidebarBodyProps
  extends VariantProps<typeof sidebarBodyStyles>,
    React.HTMLAttributes<HTMLDivElement> {}

const SidebarBody = ({
  children,
  className,
  ...props
}: React.PropsWithChildren<SidebarBodyProps>) => {
  return (
    <div className={sidebarBodyStyles({ className })} {...props}>
      {children}
    </div>
  );
};

export default SidebarBody;
