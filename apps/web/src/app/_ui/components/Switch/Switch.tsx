import * as SwitchPrimitives from '@radix-ui/react-switch';
import { ComponentProps } from 'react';
import { VariantProps, tv } from 'tailwind-variants';

const switchStyles = tv({
  slots: {
    wrapper:
      'focus-visible:outline-hidden data-[state=unchecked]:bg-fill-primary-selected peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent bg-fill-brand transition-colors focus-visible:ring-2 focus-visible:ring-border-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
    thumb:
      'pointer-events-none block size-5 rounded-full shadow-sm ring-0 transition-transform data-[state=checked]:translate-x-full data-[state=unchecked]:translate-x-0'
  },
  variants: {
    size: {
      sm: { wrapper: 'h-4 w-7', thumb: 'size-3' },
      md: { wrapper: 'h-6 w-11', thumb: 'size-5' }
    },
    colorRole: {
      brand: {
        wrapper: 'bg-fill-brand data-[state=checked]:bg-fill-brand',
        thumb: 'bg-text-primary-on-fill dark:bg-text-primary'
      },
      warning: {
        wrapper: 'bg-fill-warning data-[state=checked]:bg-fill-warning',
        thumb: 'bg-text-warning-on-fill'
      },
      success: {
        wrapper: 'bg-fill-success data-[state=checked]:bg-fill-success',
        thumb: 'bg-text-success-on-fill'
      }
    }
  },
  defaultVariants: {
    size: 'md',
    colorRole: 'brand'
  }
});

export interface SwitchProps
  extends ComponentProps<typeof SwitchPrimitives.Root>,
    VariantProps<typeof switchStyles> {}

const { wrapper, thumb } = switchStyles();

const Switch = ({ size, colorRole, className, ...props }: SwitchProps) => {
  return (
    <SwitchPrimitives.Root
      {...props}
      className={wrapper({ className, colorRole, size })}
    >
      <SwitchPrimitives.Thumb className={thumb({ colorRole, size })} />
    </SwitchPrimitives.Root>
  );
};

export default Switch;
