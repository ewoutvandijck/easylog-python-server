'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useMemo } from 'react';
import { VariantProps, tv } from 'tailwind-variants';

import Button, { ButtonProps } from '../Button/Button';

export const navigationItemStyles = tv({
  base: 'font-normal',
  variants: {
    isActive: {
      true: 'text-text-primary',
      false: 'text-text-muted'
    }
  },
  defaultVariants: {}
});

export interface NavigationItemProps
  extends Omit<ButtonProps, 'asChild' | 'colorRole' | 'variant'>,
    VariantProps<typeof navigationItemStyles> {
  className?: string;
  href: string;
  matchHash?: boolean;
  matchPartial?: string;
  isActive?: boolean;
  onActiveChange?: (isActive: boolean) => void;
}

const NavigationItem = ({
  className,
  matchPartial,
  isActive,
  onActiveChange,
  href,
  children,
  ...props
}: React.PropsWithChildren<NavigationItemProps>) => {
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
    <Button
      {...props}
      asChild
      size="lg"
      isToggled={isActive || isRouteActive}
      variant="ghost"
      colorRole="primary"
      className={navigationItemStyles({
        isActive: isActive || isRouteActive,
        className
      })}
    >
      <Link href={href}>{children}</Link>
    </Button>
  );
};

export default NavigationItem;
