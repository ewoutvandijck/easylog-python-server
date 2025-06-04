'use client';

import * as DropdownMenuPrimitive from '@radix-ui/react-dropdown-menu';
import { VariantProps, tv } from 'tailwind-variants';

const dropdownMenuSeparatorStyles = tv({
  base: '-mx-1 my-1 h-px bg-border-primary'
});

export interface DropdownMenuSeparatorProps
  extends React.ComponentProps<typeof DropdownMenuPrimitive.Separator>,
    VariantProps<typeof dropdownMenuSeparatorStyles> {}

const DropdownMenuSeparator = ({
  className,
  ...props
}: DropdownMenuSeparatorProps) => (
  <DropdownMenuPrimitive.Separator
    className={dropdownMenuSeparatorStyles({ className })}
    {...props}
  />
);

export default DropdownMenuSeparator;
