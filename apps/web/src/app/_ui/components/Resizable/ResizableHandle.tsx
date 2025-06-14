'use client';

import { IconGripVertical } from '@tabler/icons-react';
import * as ResizablePrimitive from 'react-resizable-panels';
import { VariantProps, tv } from 'tailwind-variants';

import Icon from '../Icon/Icon';

export const resizableHandleStyles = tv({
  slots: {
    wrapper:
      'focus-visible:outline-hidden group relative flex w-px items-center justify-center transition-all after:absolute after:inset-y-0 after:left-1/2 after:w-3 after:-translate-x-1/2 hover:brightness-95 focus-visible:ring-1 focus-visible:ring-border-primary focus-visible:ring-offset-1 data-[panel-group-direction=vertical]:h-px data-[panel-group-direction=vertical]:w-full data-[resize-handle-state=drag]:bg-border-brand data-[panel-group-direction=vertical]:after:left-0 data-[panel-group-direction=vertical]:after:h-1 data-[panel-group-direction=vertical]:after:w-full data-[panel-group-direction=vertical]:after:-translate-y-1/2 data-[panel-group-direction=vertical]:after:translate-x-0 [&[data-panel-group-direction=vertical]>div]:rotate-90',
    handle:
      'z-10 flex h-4 w-3 items-center justify-center rounded-sm border opacity-0 transition-all group-data-[resize-handle-state=hover]:bg-border-primary group-data-[resize-handle-state=drag]:opacity-100 group-data-[resize-handle-state=hover]:opacity-100'
  },
  variants: {
    colorRole: {
      primary: {
        wrapper: 'bg-border-primary',
        handle:
          'bg-border-primary group-data-[resize-handle-state=drag]:bg-border-primary'
      },
      muted: {
        wrapper: 'bg-border-muted',
        handle:
          'bg-border-muted group-data-[resize-handle-state=drag]:bg-border-muted'
      }
    }
  },
  defaultVariants: {
    colorRole: 'primary'
  }
});

export interface ResizableHandleProps
  extends React.ComponentProps<typeof ResizablePrimitive.PanelResizeHandle>,
    VariantProps<typeof resizableHandleStyles> {
  withHandle?: boolean;
}

const { wrapper, handle } = resizableHandleStyles();

const ResizableHandle = ({
  children,
  className,
  withHandle = false,
  colorRole,
  ...props
}: ResizableHandleProps) => {
  return (
    <ResizablePrimitive.PanelResizeHandle
      {...props}
      className={wrapper({ className, colorRole })}
    >
      {children}

      {withHandle && (
        <div className={handle({ colorRole })}>
          <Icon icon={IconGripVertical} />
        </div>
      )}
    </ResizablePrimitive.PanelResizeHandle>
  );
};

export default ResizableHandle;
