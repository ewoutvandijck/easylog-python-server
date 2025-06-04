'use client';

import * as AlertDialogPrimitive from '@radix-ui/react-alert-dialog';
import { VariantProps } from 'tailwind-variants';

import { dialogOverlayStyles } from '../Dialog/DialogOverlay';

export interface AlertDialogOverlayProps
  extends VariantProps<typeof dialogOverlayStyles>,
    React.ComponentProps<typeof AlertDialogPrimitive.Overlay> {}

const AlertDialogOverlay = ({
  className,
  ...props
}: AlertDialogOverlayProps) => (
  <AlertDialogPrimitive.Overlay
    className={dialogOverlayStyles({ className })}
    {...props}
  />
);

export default AlertDialogOverlay;
