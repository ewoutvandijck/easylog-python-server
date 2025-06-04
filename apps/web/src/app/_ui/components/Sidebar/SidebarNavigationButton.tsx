'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import SidebarButton, { SidebarButtonProps } from './SidebarButton';

export interface SidebarNavigationButtonProps extends SidebarButtonProps {
  href: string;
  isActiveRegex?: RegExp;
}

const SidebarNavigationButton = ({
  href,
  isActiveRegex,
  children,
  ...props
}: React.PropsWithChildren<SidebarNavigationButtonProps>) => {
  const pathname = usePathname();

  const isActive = isActiveRegex
    ? isActiveRegex.test(pathname)
    : pathname === href;

  return (
    <SidebarButton asChild isToggled={isActive} {...props}>
      <Link href={href}>{children}</Link>
    </SidebarButton>
  );
};

export default SidebarNavigationButton;
