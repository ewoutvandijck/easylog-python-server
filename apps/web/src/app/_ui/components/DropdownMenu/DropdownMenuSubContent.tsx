'use client';

import * as DropdownMenuPrimitive from '@radix-ui/react-dropdown-menu';
import { VariantProps } from 'tailwind-variants';

import { dropdownMenuContentStyles } from './DropdownMenuContent';

export interface DropdownMenuSubContentProps
  extends React.ComponentProps<typeof DropdownMenuPrimitive.SubContent>,
    VariantProps<typeof dropdownMenuContentStyles> {}

const DropdownMenuSubContent = ({
  className,
  sideOffset = 6,
  ...props
}: DropdownMenuSubContentProps) => (
  <DropdownMenuPrimitive.SubContent
    className={dropdownMenuContentStyles({ className })}
    sideOffset={sideOffset}
    {...props}
  />
);

export default DropdownMenuSubContent;
