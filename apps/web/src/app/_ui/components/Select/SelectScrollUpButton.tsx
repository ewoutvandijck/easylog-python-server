'use client';

import * as SelectPrimitive from '@radix-ui/react-select';
import { IconChevronUp } from '@tabler/icons-react';
import { VariantProps, tv } from 'tailwind-variants';

import Icon from '../Icon/Icon';

const selectScrollUpButtonStyles = tv({
  base: 'flex cursor-default items-center justify-center py-1'
});

export interface SelectScrollUpButtonProps
  extends VariantProps<typeof selectScrollUpButtonStyles>,
    React.ComponentProps<typeof SelectPrimitive.SelectScrollUpButton> {}

const SelectScrollUpButton = ({
  className,
  ...props
}: SelectScrollUpButtonProps) => {
  return (
    <SelectPrimitive.ScrollUpButton
      className={selectScrollUpButtonStyles({ className })}
      {...props}
    >
      <Icon icon={IconChevronUp} />
    </SelectPrimitive.ScrollUpButton>
  );
};

export default SelectScrollUpButton;
