'use client';
import { VariantProps, tv } from 'tailwind-variants';

import useSidebarContext from '@/app/_ui/components/Sidebar/hooks/useSidebarContext';

const pageHeaderStyles = tv({
  base: 'border-border-muted bg-surface-primary sticky top-0 z-10 flex min-h-12 w-full items-center justify-between border-b pl-1.5 pr-1.5',
  variants: {
    isCollapsed: {
      false: 'lg:pl-4'
    }
  }
});

export interface PageHeaderProps
  extends VariantProps<typeof pageHeaderStyles>,
    React.HTMLAttributes<HTMLDivElement> {}

const PageHeader = ({
  className,
  children,
  ...props
}: React.PropsWithChildren<PageHeaderProps>) => {
  const { isCollapsed } = useSidebarContext();

  return (
    <header className={pageHeaderStyles({ className, isCollapsed })} {...props}>
      {children}
    </header>
  );
};

export default PageHeader;
