'use client';

import * as SelectPrimitive from '@radix-ui/react-select';
import { VariantProps, tv } from 'tailwind-variants';

const selectSeparatorStyles = tv({
  base: '-mx-1 my-1 h-px bg-border-primary'
});

export interface SelectSeparatorProps
  extends React.ComponentProps<typeof SelectPrimitive.Separator>,
    VariantProps<typeof selectSeparatorStyles> {}

const SelectSeparator = ({ className, ...props }: SelectSeparatorProps) => (
  <SelectPrimitive.Separator
    className={selectSeparatorStyles({ className })}
    {...props}
  />
);

export default SelectSeparator;
