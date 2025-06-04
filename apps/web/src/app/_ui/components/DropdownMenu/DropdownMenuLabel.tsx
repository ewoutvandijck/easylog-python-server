'use client';

import * as DropdownMenuPrimitive from '@radix-ui/react-dropdown-menu';
import { VariantProps, tv } from 'tailwind-variants';

import Typography from '../Typography/Typography';

export const dropdownMenuLabelStyles = tv({
  base: 'p-2.5',
  variants: {
    inset: {
      true: { wrapper: 'pl-8' }
    }
  },
  defaultVariants: {
    inset: false
  }
});

export interface DropdownMenuLabelProps
  extends React.ComponentProps<typeof DropdownMenuPrimitive.SubTrigger>,
    VariantProps<typeof dropdownMenuLabelStyles> {}

const DropdownMenuLabel = ({
  className,
  inset,
  children,
  ...props
}: DropdownMenuLabelProps) => (
  <Typography
    asChild
    className={dropdownMenuLabelStyles({ inset, className })}
    variant="bodySm"
    colorRole="muted"
  >
    <DropdownMenuPrimitive.Label {...props}>
      {children}
    </DropdownMenuPrimitive.Label>
  </Typography>
);

export default DropdownMenuLabel;
