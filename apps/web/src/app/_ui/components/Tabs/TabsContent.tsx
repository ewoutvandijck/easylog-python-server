'use client';

import * as TabsPrimitive from '@radix-ui/react-tabs';
import { VariantProps, tv } from 'tailwind-variants';

const tabsContentStyles = tv({
  base: 'focus-visible:outline-hidden ring-offset-white focus-visible:ring-2 focus-visible:ring-border-primary focus-visible:ring-offset-2'
});

export interface TabsContentProps
  extends VariantProps<typeof tabsContentStyles>,
    React.ComponentProps<typeof TabsPrimitive.Content> {}

const TabsContent = ({
  children,
  className,
  ...props
}: React.PropsWithChildren<TabsContentProps>) => {
  return (
    <TabsPrimitive.Content
      className={tabsContentStyles({ className })}
      {...props}
    >
      {children}
    </TabsPrimitive.Content>
  );
};

export default TabsContent;
