'use client';

import * as AlertDialogPrimitive from '@radix-ui/react-alert-dialog';

import Typography, { TypographyProps } from '../Typography/Typography';

export interface AlertDialogTitleProps
  extends TypographyProps,
    React.ComponentProps<typeof AlertDialogPrimitive.Title> {}

const AlertDialogTitle = ({
  className,
  children,
  ...props
}: AlertDialogTitleProps) => (
  <Typography asChild variant="headingMd" className={className} {...props}>
    <AlertDialogPrimitive.Title>{children}</AlertDialogPrimitive.Title>
  </Typography>
);

export default AlertDialogTitle;
