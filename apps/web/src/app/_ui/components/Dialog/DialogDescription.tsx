'use client';

import * as DialogPrimitive from '@radix-ui/react-dialog';
import { VariantProps, tv } from 'tailwind-variants';

import Typography, { TypographyProps } from '../Typography/Typography';

export const dialogDescriptionStyles = tv({
  base: 'max-w-prose'
});

export interface DialogDescriptionProps
  extends TypographyProps,
    React.ComponentProps<typeof DialogPrimitive.Description>,
    VariantProps<typeof dialogDescriptionStyles> {}

const DialogDescription = ({
  children,
  className,
  ...props
}: DialogDescriptionProps) => (
  <Typography
    asChild
    variant="bodyMd"
    colorRole="muted"
    className={dialogDescriptionStyles({ className })}
    {...props}
  >
    <DialogPrimitive.Description>{children}</DialogPrimitive.Description>
  </Typography>
);

export default DialogDescription;
