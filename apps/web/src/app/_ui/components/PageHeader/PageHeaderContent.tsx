import { VariantProps, tv } from 'tailwind-variants';

import PageHeaderExpandSidebarButton from './PageHeaderExpandSidebarButton';

const pageHeaderContentStyles = tv({
  base: 'flex items-center gap-2'
});

export interface PageHeaderContentProps
  extends VariantProps<typeof pageHeaderContentStyles>,
    React.HTMLAttributes<HTMLDivElement> {}

const PageHeaderContent = ({
  children,
  className,
  ...props
}: React.PropsWithChildren<PageHeaderContentProps>) => {
  return (
    <div className={pageHeaderContentStyles({ className })} {...props}>
      <PageHeaderExpandSidebarButton />
      {children}
    </div>
  );
};

export default PageHeaderContent;
