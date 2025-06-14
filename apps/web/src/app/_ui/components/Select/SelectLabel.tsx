'use client';

import * as SelectPrimitive from '@radix-ui/react-select';
import { VariantProps, tv } from 'tailwind-variants';

import Typography, { TypographyProps } from '../Typography/Typography';

const selectLabelStyles = tv({
  base: 'py-1.5 pl-8 pr-2'
});

export interface SelectLabelProps
  extends VariantProps<typeof selectLabelStyles>,
    React.ComponentProps<typeof SelectPrimitive.SelectLabel>,
    Omit<TypographyProps, 'variant' | 'asChild'> {}

const SelectLabel = ({ className, children, ...props }: SelectLabelProps) => {
  return (
    <Typography
      {...props}
      asChild
      variant="labelSm"
      className={selectLabelStyles({ className })}
    >
      <SelectPrimitive.Label>{children}</SelectPrimitive.Label>
    </Typography>
  );
};

export default SelectLabel;
