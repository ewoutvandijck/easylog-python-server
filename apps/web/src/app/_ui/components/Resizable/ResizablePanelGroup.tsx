'use client';

import * as ResizablePrimitive from 'react-resizable-panels';
import { VariantProps, tv } from 'tailwind-variants';

export const resizablePanelGroupStyles = tv({
  base: 'flex grow data-[panel-group-direction=vertical]:flex-col'
});

export interface ResizablePanelGroupProps
  extends React.ComponentProps<typeof ResizablePrimitive.PanelGroup>,
    VariantProps<typeof resizablePanelGroupStyles> {}

const ResizablePanelGroup = ({
  children,
  className,
  ...props
}: ResizablePanelGroupProps) => {
  return (
    <ResizablePrimitive.PanelGroup
      {...props}
      className={resizablePanelGroupStyles({ className })}
    >
      {children}
    </ResizablePrimitive.PanelGroup>
  );
};

export default ResizablePanelGroup;
