'use client';

import * as AlertDialogPrimitive from '@radix-ui/react-alert-dialog';
import { VariantProps } from 'tailwind-variants';

import AlertDialogOverlay from './AlertDialogOverlay';
import AlertDialogPortal from './AlertDialogPortal';
import { dialogContentStyles } from '../Dialog/DialogContent';

export interface AlertDialogContentProps
  extends VariantProps<typeof dialogContentStyles>,
    React.ComponentProps<typeof AlertDialogPrimitive.Content> {}

const { wrapper, content } = dialogContentStyles();

const AlertDialogContent = ({
  className,
  children,
  ...props
}: AlertDialogContentProps) => (
  <AlertDialogPortal>
    <AlertDialogOverlay />
    <AlertDialogPrimitive.Content className={wrapper({ className })} {...props}>
      <div className={content()}>{children}</div>
    </AlertDialogPrimitive.Content>
  </AlertDialogPortal>
);

export default AlertDialogContent;
