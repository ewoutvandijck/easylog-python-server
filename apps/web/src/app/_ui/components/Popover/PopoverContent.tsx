'use client';

import * as PopoverPrimitive from '@radix-ui/react-popover';
import { VariantProps, tv } from 'tailwind-variants';

export const popoverContentStyles = tv({
  base: 'shadow-xs outline-hidden border-border-primary bg-surface-primary text-text-primary data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 z-50 rounded-lg border p-4'
});

export interface PopoverContentProps
  extends VariantProps<typeof popoverContentStyles>,
    React.ComponentProps<typeof PopoverPrimitive.PopoverContent> {}

const PopoverContent = ({
  className,
  align = 'center',
  sideOffset = 4,
  ...props
}: PopoverContentProps) => (
  <PopoverPrimitive.Portal>
    <PopoverPrimitive.Content
      className={popoverContentStyles({ className })}
      sideOffset={sideOffset}
      align={align}
      {...props}
    />
  </PopoverPrimitive.Portal>
);

export default PopoverContent;
