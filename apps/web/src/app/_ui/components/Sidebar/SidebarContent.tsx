import { VariantProps, tv } from 'tailwind-variants';

export const sidebarContentStyles = tv({
  base: 'flex min-h-0 flex-1 flex-col overflow-auto'
});

export interface SidebarContentProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof sidebarContentStyles> {}

const SidebarContent = ({
  className,
  children,
  ...props
}: SidebarContentProps) => {
  return (
    <div className={sidebarContentStyles({ className })} {...props}>
      {children}
    </div>
  );
};

export default SidebarContent;
