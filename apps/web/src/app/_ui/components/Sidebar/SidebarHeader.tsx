import { type VariantProps, tv } from 'tailwind-variants';

export const sidebarHeaderStyles = tv({
  base: 'flex flex-col gap-1 px-1'
});

export interface SidebarHeaderProps
  extends VariantProps<typeof sidebarHeaderStyles>,
    React.HTMLAttributes<HTMLDivElement> {}

const SidebarHeader = ({
  children,
  className,
  ...props
}: React.PropsWithChildren<SidebarHeaderProps>) => {
  return (
    <div className={sidebarHeaderStyles({ className })} {...props}>
      {children}
    </div>
  );
};

export default SidebarHeader;
