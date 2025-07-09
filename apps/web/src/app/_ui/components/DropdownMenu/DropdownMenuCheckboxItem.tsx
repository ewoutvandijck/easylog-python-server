'use client';

import * as DropdownMenuPrimitive from '@radix-ui/react-dropdown-menu';
import { IconCheck } from '@tabler/icons-react';
import { VariantProps, tv } from 'tailwind-variants';

import Icon from '../Icon/Icon';
import Typography from '../Typography/Typography';

export const dropdownMenuCheckboxItemStyles = tv({
  slots: {
    wrapper:
      'outline-hidden data-disabled:pointer-events-none data-disabled:opacity-50 relative flex cursor-pointer select-none items-center gap-1.5 rounded-lg bg-fill-primary px-2.5 py-1.5 transition-colors hover:brightness-95 focus:text-text-primary focus:brightness-95 active:brightness-90',
    indicatorWrapper: 'flex size-3.5 items-center justify-center'
  },
  variants: {
    size: {
      md: { wrapper: 'h-8' },
      lg: { wrapper: 'h-9' }
    }
  },
  defaultVariants: {
    size: 'md'
  }
});

export interface DropdownMenuCheckboxItemProps
  extends React.ComponentProps<typeof DropdownMenuPrimitive.CheckboxItem>,
    VariantProps<typeof dropdownMenuCheckboxItemStyles> {}

const { wrapper, indicatorWrapper } = dropdownMenuCheckboxItemStyles();

const DropdownMenuCheckboxItem = ({
  className,
  children,
  size,
  ...props
}: DropdownMenuCheckboxItemProps) => (
  <Typography variant="bodySm" asChild>
    <DropdownMenuPrimitive.CheckboxItem
      className={wrapper({ className, size })}
      {...props}
    >
      {children}
      <DropdownMenuPrimitive.ItemIndicator>
        <span className={indicatorWrapper()}>
          <Icon colorRole="muted" icon={IconCheck} />
        </span>
      </DropdownMenuPrimitive.ItemIndicator>
    </DropdownMenuPrimitive.CheckboxItem>
  </Typography>
);

export default DropdownMenuCheckboxItem;
