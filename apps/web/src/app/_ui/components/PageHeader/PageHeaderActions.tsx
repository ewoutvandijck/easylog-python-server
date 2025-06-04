import { VariantProps, tv } from 'tailwind-variants';

const pageHeaderActionStyles = tv({
  base: 'flex items-center gap-2'
});

export interface PageHeaderActionsProps
  extends VariantProps<typeof pageHeaderActionStyles>,
    React.HTMLAttributes<HTMLDivElement> {}

const PageHeaderActions = ({
  children,
  className,
  ...props
}: PageHeaderActionsProps) => {
  return (
    <div className={pageHeaderActionStyles({ className })} {...props}>
      {children}
    </div>
  );
};

export default PageHeaderActions;
