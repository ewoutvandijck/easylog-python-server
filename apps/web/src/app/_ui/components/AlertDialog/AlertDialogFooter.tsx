'use client';

import { VariantProps } from 'tailwind-variants';

import { dialogFooterStyles } from '../Dialog/DialogFooter';

export interface AlertDialogFooterProps
  extends VariantProps<typeof dialogFooterStyles> {
  className?: string;
}

const AlertDialogFooter = ({
  className,
  children,
  ...props
}: React.PropsWithChildren<AlertDialogFooterProps>) => (
  <div className={dialogFooterStyles({ className, ...props })}>{children}</div>
);

export default AlertDialogFooter;
