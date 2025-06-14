'use client';

import { VariantProps, tv } from 'tailwind-variants';

export const dialogFooterStyles = tv({
  base: 'flex shrink-0 items-center justify-end gap-2 border-t border-border-muted bg-surface-muted p-2'
});

export interface DialogFooterProps
  extends VariantProps<typeof dialogFooterStyles> {
  className?: string;
}

const DialogFooter = ({
  className,
  children,
  ...props
}: React.PropsWithChildren<DialogFooterProps>) => (
  <div className={dialogFooterStyles({ className, ...props })}>{children}</div>
);

export default DialogFooter;
