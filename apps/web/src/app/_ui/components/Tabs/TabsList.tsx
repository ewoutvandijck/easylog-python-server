'use client';

import * as TabsPrimitive from '@radix-ui/react-tabs';
import { VariantProps, tv } from 'tailwind-variants';

const tabsListStyles = tv({
  base: 'bg-fill-muted/25 text-text-muted inline-flex items-center justify-center py-1',
  variants: {
    shape: {
      rect: 'rounded-xl',
      pill: 'rounded-full'
    }
  },
  defaultVariants: {
    shape: 'rect'
  }
});

export interface TabsListProps
  extends VariantProps<typeof tabsListStyles>,
    React.ComponentProps<typeof TabsPrimitive.List> {}

const TabsList = ({
  children,
  shape,
  className,
  ...props
}: React.PropsWithChildren<TabsListProps>) => {
  return (
    <TabsPrimitive.List
      className={tabsListStyles({ className, shape })}
      {...props}
    >
      {children}
    </TabsPrimitive.List>
  );
};

export default TabsList;
