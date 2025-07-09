'use client';

import * as TabsPrimitive from '@radix-ui/react-tabs';
import { VariantProps, tv } from 'tailwind-variants';

const tabsTriggerStyles = tv({
  base: 'focus-visible:outline-hidden data-[state=active]:shadow-xs focus-visible:ring-border-primary data-[state=active]:border-border-primary data-[state=active]:bg-fill-primary data-[state=active]:text-text-primary inline-flex shrink-0 items-center justify-center whitespace-nowrap border border-transparent text-sm font-medium ring-offset-white transition-all focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  variants: {
    shape: {
      rect: 'rounded-lg',
      pill: 'rounded-full'
    },
    size: {
      sm: 'h-8 px-2',
      md: 'h-9 px-2.5',
      lg: 'h-10 px-3'
    }
  },
  defaultVariants: {
    shape: 'rect',
    size: 'md'
  }
});

export interface TabsTriggerProps
  extends VariantProps<typeof tabsTriggerStyles>,
    React.ComponentProps<typeof TabsPrimitive.Trigger> {}

const TabsTrigger = ({
  children,
  className,
  size,
  shape,
  ...props
}: React.PropsWithChildren<TabsTriggerProps>) => {
  return (
    <TabsPrimitive.Trigger
      className={tabsTriggerStyles({ className, size, shape })}
      {...props}
    >
      {children}
    </TabsPrimitive.Trigger>
  );
};

export default TabsTrigger;
