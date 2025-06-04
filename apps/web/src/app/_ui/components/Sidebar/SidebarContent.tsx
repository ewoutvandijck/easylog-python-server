'use client';

import { VariantProps, tv } from 'tailwind-variants';

export const sidebarContentStyles = tv({
  base: 'flex h-full w-full flex-col justify-between gap-1'
});

export interface SidebarContentProps
  extends VariantProps<typeof sidebarContentStyles>,
    React.HTMLAttributes<HTMLDivElement> {}

const SidebarContent = ({
  children,
  className
}: React.PropsWithChildren<SidebarContentProps>) => {
  return <div className={sidebarContentStyles({ className })}>{children}</div>;
};

export default SidebarContent;
