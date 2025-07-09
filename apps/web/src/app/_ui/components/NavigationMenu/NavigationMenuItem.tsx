'use client';

import { useEffect, useRef } from 'react';
import { VariantProps, tv } from 'tailwind-variants';

import Typography, {
  TypographyProps
} from '@/app/_ui/components/Typography/Typography';
import useNavigationMenuContext from '@/app/_ui/hooks/useNavigationMenuContext';
import { Link, usePathname } from '@/i18n/routing';

export const navigationMenuItemStyles = tv({
  slots: {
    wrapper: 'not-last:group-data-[dir=vertical]/nav:pb-2 group',
    link: 'relative z-10 flex w-full items-center text-text-muted transition-colors group-hover:text-text-primary'
  },
  variants: {
    size: {
      xs: { link: 'h-7 px-2' },
      sm: { link: 'h-8 px-2.5' },
      md: { link: 'h-9 px-3' },
      lg: { link: 'h-10 px-3.5' }
    },
    isActive: {
      true: { link: 'text-text-primary' }
    }
  },
  defaultVariants: {
    size: 'md',
    isActive: false
  }
});

const { wrapper: wrapperStyles, link: linkStyles } = navigationMenuItemStyles();

export interface NavigationMenuItemProps
  extends VariantProps<typeof navigationMenuItemStyles>,
    React.ComponentProps<typeof Link> {
  href: string;
  matchPath?: string;
  className?: string;
  variant?: TypographyProps['variant'];
}

const NavigationMenuItem = ({
  href,
  matchPath,
  className,
  variant = 'bodySm',
  size = 'md',
  isActive: _isActive,
  children,
  ...props
}: React.PropsWithChildren<NavigationMenuItemProps>) => {
  const { hash, setHoverElement, setSelectedElement } =
    useNavigationMenuContext();

  const ref = useRef<HTMLAnchorElement>(null);

  const path = usePathname();

  const fullPath = hash ? `${path}${hash}` : path;

  const isActive =
    _isActive !== undefined ? _isActive : fullPath.endsWith(matchPath ?? href);

  useEffect(() => {
    if (isActive && ref.current) {
      setSelectedElement(ref.current);
    }
  }, [isActive, path, setSelectedElement, ref]);

  return (
    <div
      className={wrapperStyles({ isActive, className })}
      onPointerEnter={(e) => setHoverElement(e.currentTarget)}
      onPointerLeave={() => setHoverElement(null)}
    >
      <Typography variant={variant} className="text-center" asChild>
        <Link
          href={href}
          ref={ref}
          className={linkStyles({ isActive, size })}
          onClick={() => {
            /**
             * Stupid hack so that the hashchange event is triggered. Next.js
             * doesn't trigger it somehow.
             */
            const url = new URL(href, window.location.href);
            if (url.hash) {
              window.location.hash = url.hash;
            }
            setSelectedElement(ref.current);
          }}
          {...props}
        >
          {children}
        </Link>
      </Typography>
    </div>
  );
};

export default NavigationMenuItem;
