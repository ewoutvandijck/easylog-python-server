'use client';

import * as DialogPrimitive from '@radix-ui/react-dialog';

import Typography, { TypographyProps } from '../Typography/Typography';

export interface DialogTitleProps
  extends TypographyProps,
    React.ComponentProps<typeof DialogPrimitive.Title> {}

const DialogTitle = ({ className, children, ...props }: DialogTitleProps) => (
  <Typography asChild variant="headingSm" className={className} {...props}>
    <DialogPrimitive.Title>{children}</DialogPrimitive.Title>
  </Typography>
);

export default DialogTitle;
