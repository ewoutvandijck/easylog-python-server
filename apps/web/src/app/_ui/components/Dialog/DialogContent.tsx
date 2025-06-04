'use client';

import * as DialogPrimitive from '@radix-ui/react-dialog';
import { VariantProps, tv } from 'tailwind-variants';

import DialogOverlay from './DialogOverlay';
import DialogPortal from './DialogPortal';

export const dialogContentStyles = tv({
  slots: {
    wrapper:
      'outline-hidden data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-bottom-[33%] data-[state=open]:slide-in-from-bottom-[33%] pointer-events-none fixed left-1/2 top-1/3 z-50 box-content flex max-h-[calc(100svh-1rem)] max-w-[calc(100vw-1rem)] -translate-x-1/2 -translate-y-1/3 flex-col items-center justify-center duration-200 lg:max-h-[calc(100svh-2rem)] lg:max-w-[calc(100vw-2rem)]',
    content:
      'shadow-xs border-border-primary bg-surface-primary ring-border-primary/50 flex max-h-full w-[32rem] max-w-full grow flex-col overflow-hidden rounded-lg border ring-4',
    close: 'absolute right-2 top-2'
  },
  variants: {
    isFullscreen: {
      true: {
        wrapper:
          'max-w-screen top-1/2 h-full max-h-dvh -translate-y-1/2 lg:max-h-[calc(100svh-1rem)] lg:max-w-[calc(100vw-1rem)]',
        content:
          'size-full w-screen rounded-none border-none lg:rounded-lg lg:border'
      }
    }
  }
});

export interface DialogContentProps
  extends VariantProps<typeof dialogContentStyles>,
    React.ComponentProps<typeof DialogPrimitive.Content> {
  preventClosing?: boolean;
}

const { wrapper, content } = dialogContentStyles();

const DialogContent = ({
  className,
  children,
  preventClosing = false,
  isFullscreen = false,
  ...props
}: DialogContentProps) => (
  <DialogPortal>
    <DialogOverlay />
    <DialogPrimitive.Content
      style={{
        /**
         * Fix for tooltip positioning not working in @container query
         *
         * @see https://github.com/radix-ui/primitives/issues/3143
         */
        contain: 'layout'
      }}
      className={wrapper({ isFullscreen })}
      onPointerDownOutside={(event) => {
        if (preventClosing) {
          event.preventDefault();
        }
        props.onPointerDownOutside?.(event);
      }}
      onInteractOutside={(event) => {
        if (preventClosing) {
          event.preventDefault();
        }
        props.onInteractOutside?.(event);
      }}
      {...props}
    >
      <div className={content({ className, isFullscreen })}>{children}</div>
    </DialogPrimitive.Content>
  </DialogPortal>
);

export default DialogContent;
