'use client';

import * as SelectPrimitive from '@radix-ui/react-select';
import { VariantProps, tv } from 'tailwind-variants';

import SelectScrollDownButton from './SelectScrollDownButton';
import SelectScrollUpButton from './SelectScrollUpButton';

const selectContentStyles = tv({
  slots: {
    content:
      'shadow-xs relative z-50 max-h-96 min-w-32 overflow-hidden rounded-lg border border-border-primary bg-surface-primary text-text-primary data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2',
    viewport: 'p-1'
  },
  variants: {
    position: {
      'item-aligned': null,
      popper: {
        content:
          'data-[side=bottom]:translate-y-1 data-[side=left]:-translate-x-1 data-[side=right]:translate-x-1 data-[side=top]:-translate-y-1',
        viewport:
          'h-[var(--radix-select-trigger-height)] w-full min-w-[var(--radix-select-trigger-width)]'
      }
    }
  },
  defaultVariants: {
    position: 'popper'
  }
});

export interface SelectContentProps
  extends VariantProps<typeof selectContentStyles>,
    React.ComponentProps<typeof SelectPrimitive.Content> {}

const { content, viewport } = selectContentStyles();

const SelectContent = ({
  className,
  children,
  position,
  ...props
}: SelectContentProps) => {
  return (
    <SelectPrimitive.Portal>
      <SelectPrimitive.Content
        className={content({ position, className })}
        position={position}
        {...props}
      >
        <SelectScrollUpButton />
        <SelectPrimitive.Viewport className={viewport({ position })}>
          {children}
        </SelectPrimitive.Viewport>
        <SelectScrollDownButton />
      </SelectPrimitive.Content>
    </SelectPrimitive.Portal>
  );
};

export default SelectContent;
