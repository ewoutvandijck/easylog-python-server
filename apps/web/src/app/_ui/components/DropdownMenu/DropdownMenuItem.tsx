'use client';

import * as DropdownMenuPrimitive from '@radix-ui/react-dropdown-menu';
import { VariantProps, tv } from 'tailwind-variants';

import Typography from '../Typography/Typography';

export const dropdownMenuItemStyles = tv({
  base: 'outline-hidden data-disabled:pointer-events-none data-disabled:opacity-50 relative flex cursor-pointer select-none items-center gap-1.5 rounded-lg bg-fill-primary px-2.5 py-1.5 text-sm transition-colors hover:bg-fill-muted active:bg-fill-muted active:brightness-active',
  variants: {
    colorRole: {
      primary: 'text-text-primary',
      danger: 'text-text-danger'
    },
    inset: {
      true: 'pl-8'
    },
    size: {
      md: 'h-9',
      lg: 'h-10'
    }
  },
  defaultVariants: {
    colorRole: 'primary',
    inset: false,
    size: 'md'
  }
});

export interface DropdownMenuItemProps
  extends React.ComponentProps<typeof DropdownMenuPrimitive.Item>,
    VariantProps<typeof dropdownMenuItemStyles> {}

const DropdownMenuItem = ({
  className,
  colorRole,
  inset,
  size,
  children,
  ...props
}: DropdownMenuItemProps) => (
  <Typography asChild variant="bodySm">
    <DropdownMenuPrimitive.Item
      className={dropdownMenuItemStyles({ colorRole, inset, size, className })}
      {...props}
    >
      {children}
    </DropdownMenuPrimitive.Item>
  </Typography>
);

export default DropdownMenuItem;
