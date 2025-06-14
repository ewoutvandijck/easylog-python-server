'use client';

import * as AlertDialogPrimitive from '@radix-ui/react-alert-dialog';
import { IconX } from '@tabler/icons-react';
import { VariantProps } from 'tailwind-variants';

import Button from '../Button/Button';
import ButtonContent from '../Button/ButtonContent';
import { dialogHeaderStyles } from '../Dialog/DialogHeader';
import Icon from '../Icon/Icon';

export interface AlertDialogHeaderProps
  extends VariantProps<typeof dialogHeaderStyles> {
  className?: string;
}

const { wrapper, content, close } = dialogHeaderStyles();

const AlertDialogHeader = ({
  className,
  children,
  ...props
}: React.PropsWithChildren<AlertDialogHeaderProps>) => (
  <header className={wrapper({ className, ...props })}>
    <div className={content()}>{children}</div>
    <Button
      size="sm"
      asChild
      variant="ghost"
      shape="circle"
      className={close()}
    >
      <AlertDialogPrimitive.Cancel>
        <ButtonContent>
          <Icon icon={IconX} colorRole="muted" />
          <span className="sr-only">Close</span>
        </ButtonContent>
      </AlertDialogPrimitive.Cancel>
    </Button>
  </header>
);

export default AlertDialogHeader;
