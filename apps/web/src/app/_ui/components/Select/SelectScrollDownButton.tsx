'use client';

import * as SelectPrimitive from '@radix-ui/react-select';
import { IconChevronUp } from '@tabler/icons-react';
import { VariantProps, tv } from 'tailwind-variants';

import Icon from '../Icon/Icon';

const selectScrollDownButtonStyles = tv({
  base: 'flex cursor-default items-center justify-center py-1'
});

export interface SelectScrollDownButtonProps
  extends VariantProps<typeof selectScrollDownButtonStyles>,
    React.ComponentProps<typeof SelectPrimitive.SelectScrollDownButton> {}

const SelectScrollDownButton = ({
  className,
  ...props
}: SelectScrollDownButtonProps) => {
  return (
    <SelectPrimitive.ScrollDownButton
      className={selectScrollDownButtonStyles({ className })}
      {...props}
    >
      <Icon icon={IconChevronUp} />
    </SelectPrimitive.ScrollDownButton>
  );
};

export default SelectScrollDownButton;
