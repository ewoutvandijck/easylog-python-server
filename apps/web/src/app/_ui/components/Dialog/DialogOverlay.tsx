'use client';

import * as DialogPrimitive from '@radix-ui/react-dialog';
import { VariantProps, tv } from 'tailwind-variants';

export const dialogOverlayStyles = tv({
  base: 'fixed inset-0 z-50 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0'
});

export interface DialogOverlayProps
  extends VariantProps<typeof dialogOverlayStyles>,
    React.ComponentProps<typeof DialogPrimitive.Overlay> {}

const DialogOverlay = ({ className, ...props }: DialogOverlayProps) => (
  <DialogPrimitive.Overlay
    className={dialogOverlayStyles({ className })}
    {...props}
  />
);

export default DialogOverlay;
