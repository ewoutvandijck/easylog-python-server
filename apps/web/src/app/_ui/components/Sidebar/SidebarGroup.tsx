import { VariantProps, tv } from 'tailwind-variants';

export const sidebarGroupStyles = tv({
  base: 'my-3 flex flex-col gap-0.5 px-1'
});

export interface SidebarGroupProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof sidebarGroupStyles> {}

const SidebarGroup = ({ className, children, ...props }: SidebarGroupProps) => {
  return (
    <div className={sidebarGroupStyles({ className })} {...props}>
      {children}
    </div>
  );
};

export default SidebarGroup;
