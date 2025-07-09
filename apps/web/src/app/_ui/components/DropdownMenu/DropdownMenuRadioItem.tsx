'use client';

import * as DropdownMenuPrimitive from '@radix-ui/react-dropdown-menu';
import { IconCheck } from '@tabler/icons-react';
import { VariantProps, tv } from 'tailwind-variants';

import Icon from '../Icon/Icon';
import Typography from '../Typography/Typography';

export const dropdownMenuRadioItemStyles = tv({
  slots: {
    wrapper:
      'outline-hidden data-disabled:pointer-events-none data-disabled:opacity-50 relative flex cursor-pointer select-none items-center gap-1.5 rounded-lg bg-fill-primary px-2.5 py-1.5 transition-colors hover:bg-fill-muted focus:bg-fill-muted focus:text-text-primary active:bg-fill-muted active:brightness-active',
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

export interface DropdownMenuRadioItemProps
  extends React.ComponentProps<typeof DropdownMenuPrimitive.RadioItem>,
    VariantProps<typeof dropdownMenuRadioItemStyles> {}

const { wrapper, indicatorWrapper } = dropdownMenuRadioItemStyles();

const DropdownMenuRadioItem = ({
  className,
  children,
  size,
  ...props
}: DropdownMenuRadioItemProps) => (
  <Typography variant="bodySm" asChild>
    <DropdownMenuPrimitive.RadioItem
      className={wrapper({ className, size })}
      {...props}
    >
      {children}
      <DropdownMenuPrimitive.ItemIndicator>
        <span className={indicatorWrapper()}>
          <Icon colorRole="muted" icon={IconCheck} />
        </span>
      </DropdownMenuPrimitive.ItemIndicator>
    </DropdownMenuPrimitive.RadioItem>
  </Typography>
);

export default DropdownMenuRadioItem;
