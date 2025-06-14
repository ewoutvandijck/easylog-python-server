'use client';

import { useEffect, useMemo } from 'react';

import { Link, usePathname } from '@/i18n/routing';

import SidebarMenuButton, { SidebarMenuButtonProps } from './SidebarMenuButton';

export interface SidebarNavigationItemProps extends SidebarMenuButtonProps {
  href: string;
  matchPartial?: string;
  isActive?: boolean;
  onActiveChange?: (isActive: boolean) => void;
}

const SidebarNavigationItem = ({
  href,
  matchPartial,
  isActive,
  onActiveChange,
  children,
  ...props
}: React.PropsWithChildren<SidebarNavigationItemProps>) => {
  const path = usePathname();

  const isRouteActive = useMemo(() => {
    if (matchPartial) {
      return path.includes(matchPartial);
    }

    return href.endsWith(path);
  }, [matchPartial, href, path]);

  useEffect(() => {
    if (isActive !== undefined && isRouteActive !== isActive) {
      onActiveChange?.(isRouteActive);
    }
  }, [isActive, isRouteActive, onActiveChange]);

  return (
    <SidebarMenuButton isActive={isActive || isRouteActive} {...props} asChild>
      <Link href={href}>{children}</Link>
    </SidebarMenuButton>
  );
};

export default SidebarNavigationItem;
