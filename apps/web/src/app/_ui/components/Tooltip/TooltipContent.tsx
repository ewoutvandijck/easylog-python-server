'use client';

import * as TooltipPrimitive from '@radix-ui/react-tooltip';
import { VariantProps, tv } from 'tailwind-variants';

const tooltipContentStyles = tv({
  slots: {
    content:
      'border-border-primary bg-surface-primary text-text-primary animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 z-50 max-w-[calc(100vw-2rem)] overflow-hidden rounded-md border px-2.5 py-1.5 text-center font-sans text-sm font-normal leading-5 shadow-sm data-[align=start]:text-left data-[align=end]:text-right lg:max-w-prose',
    arrow: 'fill-border-primary animate-in fade-in-0'
  }
});

export interface TooltipContentProps
  extends React.ComponentProps<typeof TooltipPrimitive.Content>,
    VariantProps<typeof tooltipContentStyles> {}

const { content, arrow } = tooltipContentStyles();

const TooltipContent = ({
  className,
  sideOffset = 4,
  collisionPadding = 12,
  children,
  ...props
}: TooltipContentProps) => {
  return (
    <TooltipPrimitive.Content
      sideOffset={sideOffset}
      collisionPadding={collisionPadding}
      className={content({ className })}
      {...props}
    >
      <TooltipPrimitive.Arrow className={arrow()} />
      {children}
    </TooltipPrimitive.Content>
  );
};

export default TooltipContent;
