import { VariantProps, tv } from 'tailwind-variants';

export const sidebarHeaderStyles = tv({
  base: 'flex flex-col gap-0.5'
});

export interface SidebarHeaderProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof sidebarHeaderStyles> {}

const SidebarHeader = ({
  className,
  children,
  ...props
}: SidebarHeaderProps) => {
  return (
    <div className={sidebarHeaderStyles({ className })} {...props}>
      {children}
    </div>
  );
};

export default SidebarHeader;
